"""JamGuard: notices when a motor-driven intake stops turning while it is being
driven, backs it out, and gives up (motor off, driver told) if it keeps jamming.

Call update(power) every loop instead of motor.setPower(power); the guard
passes the power through while things are fine. It never sleeps, so the rest of
the robot keeps running during an unjam.

Stuck means, for longer than STALL_MS, either
  - the shaft turns slower than STALL_FRACTION of the speed this motor reached
    while running freely earlier (learned at runtime, per guard, so it needs no
    gear ratio and follows the battery), or slower than MIN_TPS before anything
    was learned, or
  - the motor draws more than STALL_AMPS (HD Hex stalls at 8.5 A per REV).
Nothing is judged during GRACE_MS after the power goes from 0 to on, or after
an unjam: a motor spinning up is slow on purpose.
"""

from ftc.hardware import DcMotorEx
from ftc.navigation import CurrentUnit
from ftc.util import ElapsedTime


class JamGuard:
    IDLE: int = 0
    SPINUP: int = 1
    RUN: int = 2
    UNJAM: int = 3
    FAULT: int = 4

    GRACE_MS: float = 250.0
    STALL_MS: float = 150.0
    STALL_FRACTION: float = 0.25
    MIN_TPS: float = 50.0
    STALL_AMPS: float = 6.0
    UNJAM_MS: float = 250.0
    UNJAM_POWER: float = 1.0
    # More than MAX_UNJAMS unjams within UNJAM_WINDOW_MS means it isn't clearing.
    MAX_UNJAMS: int = 3
    UNJAM_WINDOW_MS: float = 3000.0
    # The free-running speed is only learned from power at least this high.
    LEARN_MIN_POWER: float = 0.3

    name: str
    motor: DcMotorEx
    clock: ElapsedTime
    state: int
    state_since: float
    slow_since: float
    last_power: float
    unjam_dir: float
    unjam_times: list[float]
    # Learned free-running speed, ticks/s per unit of power; 0 until known.
    free_tps_per_power: float
    velocity: float
    amps: float
    faulted_now: bool
    total_unjams: int

    def __init__(self, name: str, motor: DcMotorEx) -> None:
        self.name = name
        self.motor = motor
        self.clock = ElapsedTime()
        self.free_tps_per_power = 0.0
        self.total_unjams = 0
        self.rearm()

    def rearm(self) -> None:
        """Back to idle and forget recent unjams (e.g. when the driver turns the
        mechanism off and on again after clearing it by hand). The learned
        speed is kept."""
        self.state = self.IDLE
        self.state_since = self.clock.milliseconds()
        self.slow_since = -1.0
        self.last_power = 0.0
        self.unjam_dir = 0.0
        self.unjam_times = []
        self.velocity = 0.0
        self.amps = 0.0
        self.faulted_now = False

    def enter(self, state: int) -> None:
        self.state = state
        self.state_since = self.clock.milliseconds()
        self.slow_since = -1.0

    def in_state_ms(self) -> float:
        return self.clock.milliseconds() - self.state_since

    def is_faulted(self) -> bool:
        return self.state == self.FAULT

    def just_faulted(self) -> bool:
        """True once, on the loop the guard gave up (to rumble the gamepad)."""
        was = self.faulted_now
        self.faulted_now = False
        return was

    def stuck_threshold(self, power: float) -> float:
        if self.free_tps_per_power > 0.0:
            return max(self.MIN_TPS, self.STALL_FRACTION * self.free_tps_per_power * abs(power))
        return self.MIN_TPS

    def update(self, power: float) -> None:
        now = self.clock.milliseconds()
        if self.state == self.FAULT:
            self.motor.setPower(0.0)
            return
        if self.state == self.UNJAM:
            if self.in_state_ms() < self.UNJAM_MS:
                self.motor.setPower(self.unjam_dir * self.UNJAM_POWER)
                return
            self.enter(self.SPINUP)

        if abs(power) < 0.05:
            if self.state != self.IDLE:
                self.enter(self.IDLE)
            self.last_power = 0.0
            self.motor.setPower(0.0)
            return
        if self.state == self.IDLE:
            self.enter(self.SPINUP)
        self.last_power = power
        self.motor.setPower(power)

        self.velocity = self.motor.getVelocity()
        if self.state == self.SPINUP:
            if self.in_state_ms() >= self.GRACE_MS:
                self.enter(self.RUN)
            return

        # Speed in the commanded direction: running backwards counts as stuck.
        forward_tps = self.velocity
        if power < 0:
            forward_tps = -forward_tps
        self.amps = self.motor.getCurrent(CurrentUnit.AMPS)
        slow = forward_tps < self.stuck_threshold(power) or self.amps > self.STALL_AMPS
        if not slow:
            self.slow_since = -1.0
            if abs(power) >= self.LEARN_MIN_POWER:
                # Rise quickly, sink slowly (~10 s at 50 loops/s): a mechanism
                # grinding at 30% speed must not teach the guard that 30% is normal.
                sample = forward_tps / abs(power)
                if self.free_tps_per_power <= 0.0:
                    self.free_tps_per_power = sample
                elif sample > self.free_tps_per_power:
                    self.free_tps_per_power = 0.8 * self.free_tps_per_power + 0.2 * sample
                else:
                    self.free_tps_per_power = 0.998 * self.free_tps_per_power + 0.002 * sample
            return
        if self.slow_since < 0:
            self.slow_since = now
            return
        if now - self.slow_since < self.STALL_MS:
            return

        # Jammed: forget unjams outside the window, then back out or give up.
        recent: list[float] = []
        for t in self.unjam_times:
            if now - t < self.UNJAM_WINDOW_MS:
                recent.append(t)
        self.unjam_times = recent
        if len(self.unjam_times) >= self.MAX_UNJAMS:
            self.enter(self.FAULT)
            self.faulted_now = True
            self.motor.setPower(0.0)
            return
        self.unjam_times.append(now)
        self.total_unjams = self.total_unjams + 1
        self.unjam_dir = -1.0
        if power < 0:
            self.unjam_dir = 1.0
        self.enter(self.UNJAM)
        self.motor.setPower(self.unjam_dir * self.UNJAM_POWER)

    def status(self) -> str:
        if self.state == self.FAULT:
            return "JAMMED - clear it by hand, then turn it off and on"
        if self.state == self.UNJAM:
            return "unjamming"
        if self.state == self.SPINUP:
            return "spinning up"
        if self.state == self.RUN:
            return f"ok {self.velocity:.0f} t/s {self.amps:.1f} A"
        return "off"
