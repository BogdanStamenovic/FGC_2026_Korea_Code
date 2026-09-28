"""Main TeleOp for Gicko (FGC 2026, hardware configuration "FGC2026-Incheon").

Press INIT on the Driver Hub: everything above waitForStart() runs once.
Press START: the while loop runs until STOP.

Controls, on gamepad 1:
  left stick          drive: up = forward, sideways = strafe
  right stick X       turn
  options             heading hold on/off (on at start; 1 rumble = on, 2 = off)
  cross               MagDump: off -> spin up shooter -> shoot -> off
  circle              BallPickup on/off
                      (MagDump and BallPickup share the Collector motor: while
                      one is on, the other's button only rumbles)
  share               climbing mode on/off (1 rumble = on, 2 = off)

In climbing mode, driving works the same, the shooter and pickup are off
(entering it stops them), and:
  left bumper / left trigger     ClimbUpper up / down
  right bumper / right trigger   SecondClimbUpper up / down
                                 (bumpers full power, triggers as far as pressed)
  options             fixator release, 1 s per press, as often as needed
  dpad down / up      chain down / up (the first dpad down also drops the chain)
  cross               chain brake: engage / release, each press
  square              the left stick (up/down) runs the Climber motor instead
                      of driving; press again to drive
None of these exist outside climbing mode. Leaving it stops every climbing
motor; the chain brake stays where it is.
While the Climber runs, telemetry shows what it was told, the current it
draws, the lowest battery voltage and how many power cuts it saw (current
dropping to ~0 and coming back while the power sent stayed the same).

MANUAL MODE: the first time anything on gamepad 2 is touched, gamepad 2 takes
over for the rest of the match and gamepad 1 is ignored. Same layout, but
nothing is automatic except the collector's unjamming: no heading hold, no
calibration corrections, and the shooter feeds the moment shoot is pressed.
Climbing mode works the same on gamepad 2.

Driving uses the Calibration OpMode's measurements (drive.py); without a
calibration file it still drives, uncorrected, and says so on telemetry.

Loop speed: every hub command blocks this loop (~2-3 ms each, up to 250 ms
when the hub does not answer), and the driver's sticks and buttons are only
read once per loop. So the loop reads each hub once (bulk caching), reads the
IMU only when heading hold can use it, and builds telemetry 10 times a second.
"""

# ── pyftc:config name="FGC2026-Incheon" fingerprint="c841abeba9d5c0ab" generated="2026-09-20" ──

# ── pyftc:imports ──
from ftc.hardware import CRServo, DcMotor, DcMotorEx, DcMotorSimple, Gamepad, LynxModule, Servo, VoltageSensor
from ftc.navigation import CurrentUnit
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
    # "Collector" is both the ball collector (REVERSE) and the shooter
    # intake (FORWARD): the motor is mounted the other way round since 26 Sep.
    # The drive motors and the IMU live in OmniDrive.
    collector: DcMotorEx
    shooter: DcMotorEx
    climber: DcMotorEx
    fishing: DcMotor
    chain_drop: Servo
    chain_stop: Servo
    fixator_release: CRServo
    climb_upper: CRServo
    # ── pyftc:devices:end ──

    FLYWHEEL_POWER: float = 1.0
    # The flywheel starts in FLY_RAMP_STEPS steps over FLY_RAMP_MS instead of
    # jumping to full power: a stalled HD Hex draws ~8.5 A, and that spike
    # (with the collector) sags the battery on the Expansion Hub right when
    # the loop was seen to stall. Set FLY_RAMP_MS to 0 to start at full power.
    FLY_RAMP_MS: float = 300.0
    FLY_RAMP_STEPS: int = 4
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
    FIXATOR_POWER: float = 1.0
    FIXATOR_MS: float = 1000.0
    # The power that moves each climbing part up (flip a sign if one runs
    # the wrong way). The Climber's is applied to the left stick pushed up.
    CLIMBER_UP: float = 1.0
    CLIMB_POWER: float = -1.0
    SECOND_CLIMB_NAME: str = "SecondClimbUpper"
    SECOND_CLIMB_POWER: float = -1.0
    # How far a gamepad 2 stick or trigger must move to count as "in use".
    PAD2_TOUCH: float = 0.3
    # A power cut on the Climber: told to pull (|power| >= 0.5), current drops
    # below CUT_AMPS and is back above CUT_LOADED_AMPS within CUT_RECOVER_MS.
    # The code sends the same power throughout, so that on-off-on is
    # electrical. (A drop that stays down is just the motor running free.)
    CUT_LOADED_AMPS: float = 1.0
    CUT_AMPS: float = 0.3
    CUT_RECOVER_MS: float = 500.0
    VOLTS_EVERY_MS: float = 500.0
    TELEMETRY_EVERY_MS: float = 100.0

    cal: DriveCal
    drive: OmniDrive
    feed_guard: JamGuard
    pickup_guard: JamGuard
    clock: ElapsedTime
    hubs: list[LynxModule]
    mag_button: Cycle
    pickup_button: Cycle
    # The gamepad in charge: gamepad1, or gamepad2 once manual mode latched.
    pad: Gamepad
    manual: bool
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
    fixator_until_ms: float
    # None if "SecondClimbUpper" is not in the hub configuration.
    second_climb: CRServo
    climb_mode: bool
    climber_sticks: bool
    brake_engaged: bool
    # Climber watch, since climbing mode was entered (see watch_climber).
    climber_power: float
    climber_amps: float
    climber_peak_amps: float
    climb_volts: float
    climb_volts_low: float
    climber_loaded: bool
    # When the current dropped, or -1 while it hasn't.
    climber_dip_ms: float
    climber_cuts: int
    # This loop's button presses. Every *WasPressed() is read once per loop,
    # whatever the mode: an unread press would otherwise wait and fire later,
    # e.g. an options press from driving releasing the fixator on entering
    # climbing mode.
    press_share: bool
    press_options: bool
    press_brake: bool
    press_square: bool
    # Loop time and battery, shown so a lagging robot or a power drop can be
    # told apart from a code problem: slow loop = code, low volts = battery.
    batteries: list[VoltageSensor]
    volts: float
    volts_low: float
    volts_ms: float
    last_loop_ms: float
    loop_ms: float
    loop_worst: float
    loop_worst_shown: float
    loop_window_ms: float
    telemetry_ms: float

    def runOpMode(self) -> None:
        # ── On ready: runs once when INIT is pressed ──
        # ── pyftc:init ──
        self.collector = self.hardwareMap.get(DcMotorEx, "Collector")
        self.shooter = self.hardwareMap.get(DcMotorEx, "shooter")
        self.climber = self.hardwareMap.get(DcMotorEx, "Climber")
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
        # MANUAL: every encoder, velocity and digital read in a loop comes from
        # one bulk read per hub, cleared at the top of the loop. Without it
        # each read is its own full bulk command. The SDK sets it back to OFF
        # when the next OpMode starts.
        self.hubs = self.hardwareMap.getAll(LynxModule)
        for hub in self.hubs:
            hub.setBulkCachingMode(LynxModule.BulkCachingMode.MANUAL)
        # Set explicitly: a motor's run mode survives from the last OpMode
        # that used it, and FLYWHEEL_POWER means raw power, not a velocity.
        self.shooter.setMode(DcMotor.RunMode.RUN_WITHOUT_ENCODER)
        self.climb_upper.setDirection(DcMotorSimple.Direction.FORWARD)
        self.second_climb = self.hardwareMap.tryGet(CRServo, self.SECOND_CLIMB_NAME)
        if self.second_climb is not None:
            self.second_climb.setDirection(DcMotorSimple.Direction.FORWARD)
        self.climber.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
        # Explicit, like the shooter: the run mode survives from the last
        # OpMode, and in RUN_USING_ENCODER setPower becomes a speed target that
        # a loaded motor (or a loose encoder cable) turns into on/off chatter.
        self.climber.setMode(DcMotor.RunMode.RUN_WITHOUT_ENCODER)
        self.batteries = self.hardwareMap.getAll(VoltageSensor)
        self.volts = 0.0
        self.volts_low = 99.0
        self.volts_ms = -1.0e9
        self.last_loop_ms = 0.0
        self.loop_ms = 0.0
        self.loop_worst = 0.0
        self.loop_worst_shown = 0.0
        self.loop_window_ms = 0.0
        self.telemetry_ms = -1.0e9
        self.fishing.setDirection(DcMotorSimple.Direction.REVERSE)
        self.fishing.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)

        # Registered here, not after START: the INIT wait must not count
        # against the buttons' debounce.
        self.mag_button = Cycle(3)
        self.pickup_button = Cycle(2)
        self.pad = self.gamepad1
        self.manual = False
        self.in_use = "Free"
        self.mag_status = "off"
        self.fly_velocity = 0.0
        self.fly_ready = False
        self.prime_velocity = 0.0
        self.entered_fishing = False
        self.fixator_until_ms = 0.0
        self.climb_mode = False
        self.climber_sticks = False
        self.brake_engaged = False
        self.reset_climber_watch()
        self.press_share = False
        self.press_options = False
        self.press_brake = False
        self.press_square = False
        self.clock = ElapsedTime()

        self.telemetry.addLine("Ready. Press START.")
        self.telemetry.addLine(self.calibration_line())
        if self.second_climb is None:
            self.telemetry.addLine(f"No '{self.SECOND_CLIMB_NAME}' in the configuration: right bumper/trigger do nothing")
        self.telemetry.update()
        self.waitForStart()

        # ── On start: loops until STOP is pressed ──
        self.drive.start()
        self.chain_drop.setPosition(self.CHAIN_DROP_START)
        self.chain_stop.setPosition(self.CHAIN_STOP_START)
        self.clock.reset()
        while self.opModeIsActive():
            for hub in self.hubs:
                hub.clearBulkCache()
            now = self.clock.milliseconds()
            self.update_health(now)
            self.check_manual()
            self.read_presses()
            self.update_climbing(now)
            self.update_drive()
            self.update_buttons(now)
            self.update_mag_dump(now)
            self.update_ball_pickup()
            if now - self.telemetry_ms >= self.TELEMETRY_EVERY_MS:
                self.telemetry_ms = now
                self.show_status()
                self.telemetry.update()
        self.drive.stop()

    # ------------------------------------------------------------------ manual mode

    def check_manual(self) -> None:
        if self.manual or not self.touched(self.gamepad2):
            return
        self.manual = True
        self.pad = self.gamepad2
        self.drive.use_corrections = False
        self.drive.hold_enabled = False
        # Presses gamepad 2 made before now must not act, nor must a button
        # that is already down (e.g. the one that switched modes).
        self.gamepad2.resetEdgeDetection()
        self.mag_button.was_down = True
        self.pickup_button.was_down = True
        self.gamepad2.rumbleBlips(2)

    def touched(self, g: Gamepad) -> bool:
        t = self.PAD2_TOUCH
        if abs(g.left_stick_x) > t or abs(g.left_stick_y) > t or abs(g.right_stick_x) > t or abs(g.right_stick_y) > t:
            return True
        if g.left_trigger > t or g.right_trigger > t:
            return True
        if g.a or g.b or g.x or g.y or g.left_bumper or g.right_bumper:
            return True
        if g.dpad_up or g.dpad_down or g.dpad_left or g.dpad_right:
            return True
        return g.left_stick_button or g.right_stick_button or g.back or g.start or g.guide

    # ------------------------------------------------------------------ drive

    def read_presses(self) -> None:
        self.press_share = self.pad.backWasPressed()
        self.press_options = self.pad.optionsWasPressed()
        # Cross is the shooter's button outside climbing mode; in it, the brake's.
        self.press_brake = self.pad.crossWasPressed()
        self.press_square = self.pad.squareWasPressed()

    def update_drive(self) -> None:
        if self.climb_mode and self.climber_sticks:
            self.drive.drive(0.0, 0.0, 0.0)
            return
        if not self.manual and not self.climb_mode and self.press_options:
            self.drive.hold_enabled = not self.drive.hold_enabled
            if self.drive.hold_enabled:
                self.pad.rumbleBlips(1)
            else:
                self.pad.rumbleBlips(2)
        # The IMU is an I2C read (the slowest thing in the loop): only when
        # heading hold can use it.
        if self.drive.heading_useful():
            self.drive.update_heading()
        self.drive.teleop_gamepad(self.pad)

    # ------------------------------------------------------------------ buttons

    def update_buttons(self, now: float) -> None:
        # A mode button only steps its phase while its mode may run; otherwise
        # the press used to be remembered and fire later, e.g. the shooter
        # spinning up by itself the moment BallPickup was switched off.
        mag = self.mag_button.pressed(self.pad.cross, now)
        pickup = self.pickup_button.pressed(self.pad.circle, now)
        if self.climb_mode:
            return
        if mag:
            if self.in_use == "BallPickup":
                self.pad.rumble(150)
            else:
                self.mag_button.advance()
        if pickup:
            if self.in_use == "MagDump":
                self.pad.rumble(150)
            else:
                self.pickup_button.advance()

    # ------------------------------------------------------------------ shooter

    def update_mag_dump(self, now: float) -> None:
        phase = self.mag_button.phase
        if phase == 1 and self.in_use == "Free":
            self.collector.setDirection(DcMotorSimple.Direction.FORWARD)
            self.collector.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
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

        # The SDK only sends setPower when the value changes, so this costs
        # FLY_RAMP_STEPS commands per spin-up, not one per loop.
        step = self.FLY_RAMP_STEPS
        if self.FLY_RAMP_MS > 0:
            step = min(self.FLY_RAMP_STEPS, int((now - self.fly_start_ms) * self.FLY_RAMP_STEPS / self.FLY_RAMP_MS) + 1)
        self.shooter.setPower(self.FLYWHEEL_POWER * step / self.FLY_RAMP_STEPS)
        self.fly_velocity = abs(self.shooter.getVelocity())
        self.track_flywheel(now)
        feed = 0.0
        if phase < 2:
            self.mag_status = "flywheel ready" if self.fly_ready else "spinning up"
        elif self.manual:
            feed = self.FEED_POWER
            self.mag_status = "shooting (manual)"
        elif not self.fly_ready:
            self.mag_status = "shoot pressed, waiting for flywheel"
        elif self.fly_velocity < self.prime_velocity * self.FEED_GATE:
            self.mag_status = "flywheel recovering"
        else:
            feed = self.FEED_POWER
            self.mag_status = "shooting"
        self.feed_guard.update(feed)
        if self.feed_guard.just_faulted():
            self.pad.rumbleBlips(3)

    def track_flywheel(self, now: float) -> None:
        """Latch prime_velocity once the flywheel stops speeding up. Sampling it
        at the moment of the shoot press gave a too-low prime when the press
        came early, and the feed gate then let slow shots through."""
        if self.fly_ready or now - self.fly_start_ms < self.FLY_RAMP_MS:
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
            self.collector.setDirection(DcMotorSimple.Direction.REVERSE)
            self.pickup_guard.rearm()
            self.in_use = "BallPickup"
        elif phase == 0 and self.in_use == "BallPickup":
            self.pickup_guard.update(0.0)
            self.in_use = "Free"
        if self.in_use == "BallPickup":
            self.pickup_guard.update(self.PICKUP_POWER)
            if self.pickup_guard.just_faulted():
                self.pad.rumbleBlips(3)

    # ------------------------------------------------------------------ climbing mode

    def update_climbing(self, now: float) -> None:
        if self.press_share:
            self.climb_mode = not self.climb_mode
            if self.climb_mode:
                # Phase 0 makes MagDump/BallPickup switch themselves off this loop.
                self.mag_button.phase = 0
                self.pickup_button.phase = 0
                self.reset_climber_watch()
                self.pad.rumbleBlips(1)
            else:
                self.stop_climbing()
                self.pad.rumbleBlips(2)
        # A fixator release started in climbing mode still ends on time.
        if self.fixator_until_ms > 0 and now >= self.fixator_until_ms:
            self.fixator_release.setPower(0.0)
            self.fixator_until_ms = 0.0
        if not self.climb_mode:
            return
        g = self.pad
        if self.press_square:
            self.climber_sticks = not self.climber_sticks
        if self.press_brake:
            self.brake_engaged = not self.brake_engaged
            self.chain_stop.setPosition(self.CHAIN_STOP_ENGAGED if self.brake_engaged else self.CHAIN_STOP_START)
        if self.press_options:
            self.fixator_until_ms = now + self.FIXATOR_MS
            self.fixator_release.setPower(self.FIXATOR_POWER)
        self.climb_upper.setPower(self.climb_power(g.left_bumper, g.left_trigger, self.CLIMB_POWER))
        if self.second_climb is not None:
            self.second_climb.setPower(self.climb_power(g.right_bumper, g.right_trigger, self.SECOND_CLIMB_POWER))
        if g.dpad_down:
            self.chain_drop.setPosition(self.CHAIN_DROP_FISHING)
            self.entered_fishing = True
            self.fishing.setPower(1.0)
        elif g.dpad_up:
            self.fishing.setPower(-1.0)
        else:
            self.fishing.setPower(0.0)
        climber = 0.0
        if self.climber_sticks:
            climber = -g.left_stick_y * self.CLIMBER_UP
        self.climber.setPower(climber)
        self.climber_power = climber
        if abs(climber) > 0.01:
            self.watch_climber(climber, now)

    def reset_climber_watch(self) -> None:
        self.climber_power = 0.0
        self.climber_amps = 0.0
        self.climber_peak_amps = 0.0
        self.climb_volts = 0.0
        self.climb_volts_low = 99.0
        self.climber_loaded = False
        self.climber_dip_ms = -1.0
        self.climber_cuts = 0

    def watch_climber(self, power: float, now: float) -> None:
        """Every loop while the Climber runs: its current and the battery, two
        hub commands. Every loop and not at the 10 Hz of the rest, because a
        power cut can be shorter than 100 ms; nothing else runs while climbing."""
        self.climber_amps = self.climber.getCurrent(CurrentUnit.AMPS)
        self.climber_peak_amps = max(self.climber_peak_amps, self.climber_amps)
        if len(self.batteries) > 0:
            self.climb_volts = self.batteries[0].getVoltage()
            self.climb_volts_low = min(self.climb_volts_low, self.climb_volts)
        if abs(power) < 0.5:
            self.climber_loaded = False
            self.climber_dip_ms = -1.0
            return
        if self.climber_amps >= self.CUT_LOADED_AMPS:
            if self.climber_dip_ms >= 0 and now - self.climber_dip_ms <= self.CUT_RECOVER_MS:
                self.climber_cuts = self.climber_cuts + 1
            self.climber_loaded = True
            self.climber_dip_ms = -1.0
        elif self.climber_amps < self.CUT_AMPS and self.climber_loaded:
            self.climber_loaded = False
            self.climber_dip_ms = now

    @staticmethod
    def climb_power(up: bool, down: float, up_power: float) -> float:
        """Bumper = up at full power, trigger = down as far as it is pressed."""
        if up:
            return up_power
        return -up_power * down

    def stop_climbing(self) -> None:
        self.climber_sticks = False
        self.climb_upper.setPower(0.0)
        if self.second_climb is not None:
            self.second_climb.setPower(0.0)
        self.fishing.setPower(0.0)
        self.climber.setPower(0.0)

    # ------------------------------------------------------------------ telemetry

    def update_health(self, now: float) -> None:
        self.loop_ms = now - self.last_loop_ms
        self.last_loop_ms = now
        self.loop_worst = max(self.loop_worst, self.loop_ms)
        if now - self.loop_window_ms > 1000.0:
            self.loop_worst_shown = self.loop_worst
            self.loop_worst = 0.0
            self.loop_window_ms = now
        # Every hub reports the same battery; each read is its own hub command,
        # so twice a second is enough.
        if now - self.volts_ms >= self.VOLTS_EVERY_MS:
            self.volts_ms = now
            v = 99.0
            for b in self.batteries:
                v = min(v, b.getVoltage())
            if v < 99.0:
                self.volts = v
                self.volts_low = min(self.volts_low, v)

    def calibration_line(self) -> str:
        if self.cal.load_error != "":
            return "Drive: " + self.cal.load_error
        if not self.cal.loaded:
            return "Drive: UNCALIBRATED - run the Calibration OpMode"
        return f"Drive: calibrated ({self.cal.done_count()} of 8 steps)"

    def show_status(self) -> None:
        if self.manual:
            self.telemetry.addLine("MANUAL MODE (gamepad 2): no automation except unjamming")
        else:
            hold = "ON" if self.drive.hold_enabled else "off"
            if not self.cal.has("ramp"):
                hold = "unavailable until Calibration step 5"
            self.telemetry.addLine(self.calibration_line())
            self.telemetry.addData("Heading", f"{self.drive.heading():.1f} deg, hold {hold}")
        out = f"{100.0 * self.drive.last_output:.0f}% of stick"
        if abs(self.drive.last_correction) > 0.005:
            out = out + f", heading correction {self.drive.last_correction:+.2f}"
        self.telemetry.addData("Drive output", out)
        self.telemetry.addData("Battery", f"{self.volts:.2f} V (lowest {self.volts_low:.2f} V)")
        self.telemetry.addData("Loop", f"{self.loop_ms:.0f} ms (worst in last s: {self.loop_worst_shown:.0f} ms)")
        self.telemetry.addData("Mode", self.in_use)
        if self.in_use == "MagDump":
            self.telemetry.addData("MagDump", self.mag_status)
            self.telemetry.addData("Flywheel", f"{self.fly_velocity:.0f} t/s, prime {self.prime_velocity:.0f}")
            self.telemetry.addData("Shooter intake", self.feed_guard.status())
        if self.in_use == "BallPickup":
            self.telemetry.addData("Ball pickup", self.pickup_guard.status())
        if self.feed_guard.is_faulted() or self.pickup_guard.is_faulted():
            self.telemetry.addLine("!! Collector JAMMED - clear by hand, then press its button to turn it off and on")
        if self.climb_mode:
            self.telemetry.addLine("CLIMBING MODE (share to leave): shooter and pickup off")
            self.telemetry.addData("Sticks", "CLIMBER (square: back to driving)" if self.climber_sticks else "driving (square: Climber)")
            self.telemetry.addData("Chain brake", "ENGAGED" if self.brake_engaged else "released")
            if self.climber_peak_amps > 0:
                self.telemetry.addData("Climber", f"told {self.climber_power:+.2f}, {self.climber_amps:.1f} A (peak {self.climber_peak_amps:.1f} A), power cuts seen: {self.climber_cuts}")
                self.telemetry.addData("Battery while climbing", f"{self.climb_volts:.2f} V (lowest {self.climb_volts_low:.2f} V)")
            if self.fixator_until_ms > 0:
                self.telemetry.addLine("Fixator releasing")
