"""Flywheel and RangeFinder: the shooter pieces Main and the Calibration
OpMode's shooter step share, so "prime" and "distance" mean exactly the same
thing when the table is recorded and when it is looked up.

Flywheel: spins the shooter either at a power (Main) or at a velocity in
ticks/s (calibration), and latches `prime` once the speed stops rising.
RangeFinder: the REV 2m distance sensor "sDmeassure", median-filtered.
"""

from ftc.hardware import DcMotor, DcMotorEx, DistanceSensor
from ftc.navigation import DistanceUnit
from ftc.util import ElapsedTime


class Flywheel:
    # Settled = speed changed by less than 2% over 200 ms; after 2.5 s it
    # counts as settled regardless (a tired battery may never plateau cleanly).
    PLATEAU_MS: float = 200.0
    PLATEAU_FRACTION: float = 0.02
    SPINUP_TIMEOUT_MS: float = 2500.0
    MIN_TPS: float = 300.0

    motor: DcMotorEx
    clock: ElapsedTime
    running: bool
    velocity: float
    # Speed latched when it settled; 0 until then.
    prime: float
    ready: bool
    start_ms: float
    ref_ms: float
    ref_velocity: float

    def __init__(self, motor: DcMotorEx) -> None:
        self.motor = motor
        self.clock = ElapsedTime()
        self.running = False
        self.velocity = 0.0
        self.prime = 0.0
        self.ready = False
        self.start_ms = 0.0
        self.ref_ms = 0.0
        self.ref_velocity = 0.0

    def restart_tracking(self) -> None:
        now = self.clock.milliseconds()
        self.running = True
        self.ready = False
        self.prime = 0.0
        self.start_ms = now
        self.ref_ms = now
        self.ref_velocity = 0.0

    def spin_power(self, power: float) -> None:
        self.motor.setMode(DcMotor.RunMode.RUN_WITHOUT_ENCODER)
        self.motor.setPower(power)
        self.restart_tracking()

    def spin_velocity(self, tps: float) -> None:
        """Hold tps with the hub's velocity PID. A target the battery cannot
        reach still settles, just below the target; `prime` is what it got."""
        self.motor.setMode(DcMotor.RunMode.RUN_USING_ENCODER)
        self.motor.setVelocity(tps)
        self.restart_tracking()

    def off(self) -> None:
        self.motor.setPower(0.0)
        self.running = False
        self.ready = False

    def update(self) -> None:
        """Once per loop while running."""
        self.velocity = abs(self.motor.getVelocity())
        if not self.running or self.ready:
            return
        now = self.clock.milliseconds()
        if now - self.start_ms > self.SPINUP_TIMEOUT_MS:
            self.ready = True
            self.prime = self.velocity
            return
        if now - self.ref_ms < self.PLATEAU_MS:
            return
        change = abs(self.velocity - self.ref_velocity)
        if self.velocity > self.MIN_TPS and change < self.PLATEAU_FRACTION * self.velocity:
            self.ready = True
            self.prime = self.velocity
        self.ref_velocity = self.velocity
        self.ref_ms = now

    def rpm(self, tps: float) -> float:
        return tps * 60.0 / self.motor.getMotorType().getTicksPerRev()


class RangeFinder:
    NAME: str = "sDmeassure"
    # The sensor is rated 5..200 cm; with nothing in range it reports ~819 cm,
    # and after an I2C timeout a huge number. Neither may reach the filter.
    MIN_CM: float = 3.0
    MAX_CM: float = 220.0
    WINDOW: int = 5

    sensor: DistanceSensor
    present: bool
    recent: list[float]
    last_raw: float

    def __init__(self, sensor: DistanceSensor) -> None:
        """sensor may be None (not in the hub's configuration): everything
        then reports "no reading" instead of crashing the OpMode."""
        self.sensor = sensor
        self.present = sensor is not None
        self.recent = []
        self.last_raw = -1.0

    def update(self) -> None:
        """One I2C read (a few ms): call it only in loops that need distance."""
        if not self.present:
            return
        d = self.sensor.getDistance(DistanceUnit.CM)
        self.last_raw = d
        if d < self.MIN_CM or d > self.MAX_CM:
            return
        self.recent.append(d)
        if len(self.recent) > self.WINDOW:
            self.recent.pop(0)

    def clear(self) -> None:
        self.recent = []

    def valid(self) -> bool:
        return len(self.recent) >= 3

    def cm(self) -> float:
        """Median of the last WINDOW good readings; -1 without enough of them.
        Median, not mean: one stray reflection must not move the number."""
        if not self.valid():
            return -1.0
        return RangeFinder.median(self.recent)

    @staticmethod
    def median(values: list[float]) -> float:
        s: list[float] = []
        for d in values:
            k = 0
            while k < len(s) and s[k] < d:
                k = k + 1
            s.insert(k, d)
        return s[len(s) // 2]

    def describe(self) -> str:
        if not self.present:
            return f"no sensor '{self.NAME}' in the hub configuration"
        if not self.valid():
            return f"no reading (raw {self.last_raw:.0f} cm)"
        return f"{self.cm():.1f} cm"
