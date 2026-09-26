"""Main TeleOp for Gicko (FGC 2026, hardware configuration "FGC2026-Incheon").

Press INIT on the Driver Hub: everything above waitForStart() runs once.
Press START: the while loop runs until STOP.

Controls, all on gamepad 1:
  right stick         drive: up = forward, sideways = strafe
  left stick X        turn
  options             heading hold on/off (on at start; 1 rumble = on, 2 = off)
  cross               MagDump: off -> spin up shooter -> shoot -> off
  circle              BallPickup on/off
                      (MagDump and BallPickup share the Collector motor: while
                      one is on, the other's button only rumbles)
  dpad down / up      fishing out / in (dpad down also drops the chain)
  left bumper         chain stop (once fishing has started)
  dpad left           climb scaffold direction: up / down
  left trigger        climb scaffold power
  left stick button   fixator release (once per match)

Driving uses the Calibration OpMode's measurements (drive.py); without a
calibration file it still drives, uncorrected, and says so on telemetry.
"""

# ── pyftc:config name="FGC2026-Incheon" fingerprint="c841abeba9d5c0ab" generated="2026-09-20" ──

# ── pyftc:imports ──
from ftc.hardware import CRServo, DcMotor, DcMotorEx, DcMotorSimple, Servo
from ftc.opmode import LinearOpMode, TeleOp
from ftc.util import ElapsedTime
from drive import OmniDrive
from drive_cal import DriveCal
from jam import JamGuard
# ── pyftc:imports:end ──


class Cycle:
    """A button that steps through phases 0..count-1 and wraps, one step per
    press. A press is the moment the button goes down: holding it does nothing
    more, and a second press within DEBOUNCE_MS is ignored as contact bounce."""
    DEBOUNCE_MS: float = 250.0

    count: int
    phase: int
    last_ms: float
    was_down: bool

    def __init__(self, count: int) -> None:
        self.count = count
        self.phase = 0
        # Far in the past, so the very first press after START always counts.
        self.last_ms = -1.0e9
        self.was_down = False

    def pressed(self, down: bool, now_ms: float) -> bool:
        edge = down and not self.was_down
        self.was_down = down
        if edge and now_ms - self.last_ms > self.DEBOUNCE_MS:
            self.last_ms = now_ms
            return True
        return False

    def advance(self) -> None:
        self.phase = (self.phase + 1) % self.count


@TeleOp(name="Main", group="pyftc")
class Main(LinearOpMode):
    # ── pyftc:devices ──
    # "Collector" is both the ball collector (FORWARD) and the shooter
    # intake (REVERSE); the drive motors and the IMU live in OmniDrive.
    collector: DcMotorEx
    shooter: DcMotorEx
    climber: DcMotor
    fishing: DcMotor
    chain_drop: Servo
    chain_stop: Servo
    fixator_release: CRServo
    climb_upper: CRServo
    # ── pyftc:devices:end ──

    FLYWHEEL_POWER: float = 1.0
    FEED_POWER: float = 1.0
    PICKUP_POWER: float = 1.0
    # Feed only while the flywheel is at >= 90% of its settled speed.
    FEED_GATE: float = 0.9
    # The flywheel counts as settled when its speed changed by less than 2%
    # over 200 ms; after 2.5 s it counts as settled regardless.
    FLY_PLATEAU_MS: float = 200.0
    FLY_PLATEAU_FRACTION: float = 0.02
    FLY_SPINUP_TIMEOUT_MS: float = 2500.0
    FLY_MIN_TPS: float = 300.0
    CHAIN_DROP_START: float = 0.0
    CHAIN_DROP_FISHING: float = 0.25
    CHAIN_STOP_START: float = 0.7
    CHAIN_STOP_ENGAGED: float = 0.4
    FIXATOR_POWER: float = -1.0
    FIXATOR_MS: float = 1000.0

    cal: DriveCal
    drive: OmniDrive
    feed_guard: JamGuard
    pickup_guard: JamGuard
    clock: ElapsedTime
    mag_button: Cycle
    pickup_button: Cycle
    climb_button: Cycle
    # Who has the Collector motor: "Free", "MagDump" or "BallPickup".
    in_use: str
    mag_status: str
    fly_velocity: float
    fly_ref_velocity: float
    fly_ref_ms: float
    fly_start_ms: float
    fly_ready: bool
    prime_velocity: float
    entered_fishing: bool
    fixator_used: bool
    fixator_until_ms: float

    def runOpMode(self) -> None:
        # ── On ready: runs once when INIT is pressed ──
        # ── pyftc:init ──
        self.collector = self.hardwareMap.get(DcMotorEx, "Collector")
        self.shooter = self.hardwareMap.get(DcMotorEx, "shooter")
        self.climber = self.hardwareMap.get(DcMotor, "Climber")
        self.fishing = self.hardwareMap.get(DcMotor, "Fishing")
        self.chain_drop = self.hardwareMap.get(Servo, "chainDrop")
        self.chain_stop = self.hardwareMap.get(Servo, "ChainStop")
        self.fixator_release = self.hardwareMap.get(CRServo, "FixatorRelease")
        self.climb_upper = self.hardwareMap.get(CRServo, "ClimbUpper")
        # ── pyftc:init:end ──

        self.cal = DriveCal()
        self.cal.load()
        self.drive = OmniDrive(self.hardwareMap, self.cal)
        self.drive.init_imu()
        self.feed_guard = JamGuard("shooter intake", self.collector)
        self.pickup_guard = JamGuard("ball pickup", self.collector)
        self.fishing.setDirection(DcMotorSimple.Direction.REVERSE)
        self.fishing.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)

        # Registered here, not after START: the INIT wait must not count
        # against the buttons' debounce.
        self.mag_button = Cycle(3)
        self.pickup_button = Cycle(2)
        self.climb_button = Cycle(2)
        self.in_use = "Free"
        self.mag_status = "off"
        self.fly_velocity = 0.0
        self.fly_ready = False
        self.prime_velocity = 0.0
        self.entered_fishing = False
        self.fixator_used = False
        self.fixator_until_ms = 0.0
        self.clock = ElapsedTime()

        self.telemetry.addLine("Ready. Press START.")
        self.telemetry.addLine(self.calibration_line())
        self.telemetry.update()
        self.waitForStart()

        # ── On start: loops until STOP is pressed ──
        self.drive.start()
        self.chain_drop.setPosition(self.CHAIN_DROP_START)
        self.chain_stop.setPosition(self.CHAIN_STOP_START)
        self.clock.reset()
        while self.opModeIsActive():
            now = self.clock.milliseconds()
            self.update_drive()
            self.update_buttons(now)
            self.update_mag_dump(now)
            self.update_ball_pickup()
            self.update_fishing()
            self.update_climb()
            self.update_fixator(now)
            self.show_status()
            self.telemetry.update()
        self.drive.stop()

    # ------------------------------------------------------------------ drive

    def update_drive(self) -> None:
        if self.gamepad1.optionsWasPressed():
            self.drive.hold_enabled = not self.drive.hold_enabled
            if self.drive.hold_enabled:
                self.gamepad1.rumbleBlips(1)
            else:
                self.gamepad1.rumbleBlips(2)
        self.drive.update()
        # The calibrated drive's positive rotation turns left on this robot;
        # invert only the driver's turn stick so moving it right turns right.
        self.drive.teleop(-self.gamepad1.right_stick_y, self.gamepad1.right_stick_x, -self.gamepad1.left_stick_x)

    # ------------------------------------------------------------------ buttons

    def update_buttons(self, now: float) -> None:
        # A mode button only steps its phase while its mode may run; otherwise
        # the press used to be remembered and fire later, e.g. the shooter
        # spinning up by itself the moment BallPickup was switched off.
        if self.mag_button.pressed(self.gamepad1.cross, now):
            if self.in_use == "BallPickup":
                self.gamepad1.rumble(150)
            else:
                self.mag_button.advance()
        if self.pickup_button.pressed(self.gamepad1.circle, now):
            if self.in_use == "MagDump":
                self.gamepad1.rumble(150)
            else:
                self.pickup_button.advance()
        if self.climb_button.pressed(self.gamepad1.dpad_left, now):
            self.climb_button.advance()

    # ------------------------------------------------------------------ shooter

    def update_mag_dump(self, now: float) -> None:
        phase = self.mag_button.phase
        if phase == 1 and self.in_use == "Free":
            self.collector.setDirection(DcMotorSimple.Direction.REVERSE)
            self.collector.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
            self.shooter.setPower(self.FLYWHEEL_POWER)
            self.feed_guard.rearm()
            self.fly_ready = False
            self.fly_start_ms = now
            self.fly_ref_ms = now
            self.fly_ref_velocity = 0.0
            self.in_use = "MagDump"
        elif phase == 0 and self.in_use == "MagDump":
            self.feed_guard.update(0.0)
            self.collector.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.FLOAT)
            self.shooter.setPower(0.0)
            self.in_use = "Free"
            self.mag_status = "off"
        if self.in_use != "MagDump":
            return

        self.fly_velocity = abs(self.shooter.getVelocity())
        self.track_flywheel(now)
        feed = 0.0
        if phase < 2:
            self.mag_status = "flywheel ready" if self.fly_ready else "spinning up"
        elif not self.fly_ready:
            self.mag_status = "shoot pressed, waiting for flywheel"
        elif self.fly_velocity < self.prime_velocity * self.FEED_GATE:
            self.mag_status = "flywheel recovering"
        else:
            feed = self.FEED_POWER
            self.mag_status = "shooting"
        self.feed_guard.update(feed)
        if self.feed_guard.just_faulted():
            self.gamepad1.rumbleBlips(3)

    def track_flywheel(self, now: float) -> None:
        """Latch prime_velocity once the flywheel stops speeding up. Sampling it
        at the moment of the shoot press gave a too-low prime when the press
        came early, and the feed gate then let slow shots through."""
        if self.fly_ready:
            return
        if now - self.fly_start_ms > self.FLY_SPINUP_TIMEOUT_MS:
            self.fly_ready = True
            self.prime_velocity = self.fly_velocity
            return
        if now - self.fly_ref_ms < self.FLY_PLATEAU_MS:
            return
        change = abs(self.fly_velocity - self.fly_ref_velocity)
        if self.fly_velocity > self.FLY_MIN_TPS and change < self.FLY_PLATEAU_FRACTION * self.fly_velocity:
            self.fly_ready = True
            self.prime_velocity = self.fly_velocity
        self.fly_ref_velocity = self.fly_velocity
        self.fly_ref_ms = now

    # ------------------------------------------------------------------ pickup

    def update_ball_pickup(self) -> None:
        phase = self.pickup_button.phase
        if phase == 1 and self.in_use == "Free":
            self.collector.setDirection(DcMotorSimple.Direction.FORWARD)
            self.pickup_guard.rearm()
            self.in_use = "BallPickup"
        elif phase == 0 and self.in_use == "BallPickup":
            self.pickup_guard.update(0.0)
            self.in_use = "Free"
        if self.in_use == "BallPickup":
            self.pickup_guard.update(self.PICKUP_POWER)
            if self.pickup_guard.just_faulted():
                self.gamepad1.rumbleBlips(3)

    # ------------------------------------------------------------------ fishing, climb, fixator

    def update_fishing(self) -> None:
        if self.gamepad1.dpad_down:
            self.chain_drop.setPosition(self.CHAIN_DROP_FISHING)
            self.entered_fishing = True
            self.fishing.setPower(1.0)
        elif self.gamepad1.dpad_up:
            self.fishing.setPower(-1.0)
        else:
            self.fishing.setPower(0.0)
        # Read every loop so a press made before fishing started is not
        # remembered and applied later.
        bumper = self.gamepad1.leftBumperWasPressed()
        if bumper and self.entered_fishing:
            self.chain_stop.setPosition(self.CHAIN_STOP_ENGAGED)

    def update_climb(self) -> None:
        if self.climb_button.phase == 1:
            self.climb_upper.setDirection(DcMotorSimple.Direction.FORWARD)
        else:
            self.climb_upper.setDirection(DcMotorSimple.Direction.REVERSE)
        self.climb_upper.setPower(self.gamepad1.left_trigger)

    def update_fixator(self, now: float) -> None:
        # Timed instead of sleep(1000): sleeping froze the loop, and the drive
        # motors kept their last power for that second.
        if self.gamepad1.left_stick_button and not self.fixator_used:
            self.fixator_used = True
            self.fixator_until_ms = now + self.FIXATOR_MS
            self.fixator_release.setPower(self.FIXATOR_POWER)
        if self.fixator_until_ms > 0 and now >= self.fixator_until_ms:
            self.fixator_release.setPower(0.0)
            self.fixator_until_ms = 0.0

    # ------------------------------------------------------------------ telemetry

    def calibration_line(self) -> str:
        if self.cal.load_error != "":
            return "Drive: " + self.cal.load_error
        if not self.cal.loaded:
            return "Drive: UNCALIBRATED - run the Calibration OpMode"
        return f"Drive: calibrated ({self.cal.done_count()} of 8 steps)"

    def show_status(self) -> None:
        hold = "ON" if self.drive.hold_enabled else "off"
        if not self.cal.has("ramp"):
            hold = "unavailable until Calibration step 5"
        self.telemetry.addLine(self.calibration_line())
        self.telemetry.addData("Heading", f"{self.drive.heading():.1f} deg, hold {hold}")
        self.telemetry.addData("Mode", self.in_use)
        if self.in_use == "MagDump":
            self.telemetry.addData("MagDump", self.mag_status)
            self.telemetry.addData("Flywheel", f"{self.fly_velocity:.0f} t/s, prime {self.prime_velocity:.0f}")
            self.telemetry.addData("Shooter intake", self.feed_guard.status())
        if self.in_use == "BallPickup":
            self.telemetry.addData("Ball pickup", self.pickup_guard.status())
        if self.feed_guard.is_faulted() or self.pickup_guard.is_faulted():
            self.telemetry.addLine("!! Collector JAMMED - clear by hand, then press its button to turn it off and on")
        self.telemetry.addData("Climb dir", "UP" if self.climb_button.phase == 1 else "DOWN")
        if self.entered_fishing:
            self.telemetry.addLine("Fishing mode entered")
        if self.fixator_used:
            self.telemetry.addLine("Fixator released")
