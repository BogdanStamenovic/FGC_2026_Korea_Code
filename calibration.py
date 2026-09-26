"""Calibration: measures the drivetrain once and saves the numbers on the hub
(drive_cal.py). Main and autonomous load them at INIT; nothing has to be
re-entered after a power cycle.

Run it from the Driver Hub like any TeleOp. After START a menu lists the steps;
dpad up/down picks one, cross (A) runs it, X erases everything. Every step
explains itself on the Driver Hub before anything moves, and each accepted
step is saved on the spot, so a half-finished calibration is kept.

Order matters where noted: 1-2 need the robot on blocks (wheels in the air),
the rest on the floor. Redo 2 after changing a motor or gearbox, 3-5 after
moving the hub, 6-8 after changing wheels or carpet. Steps 9 and 10 change
nothing; they drive a 60 cm / 1 m square to show how good the numbers are.

Step 11 is the shooter, not the drive: for each test speed (ticks/s, held
by the hub's velocity PID, 1700 up in steps) the driver drives to where they
think it scores and fires single balls, answering in or missed after each.
Five in a row from one spot, then a 5-ball burst all in, and the distance
the sensor reads there is saved for that speed (shooter_cal.py). Main
rumbles when its flywheel speed and the distance match the table.

How the steps map onto the usual FTC tuning procedures:
  1 motors   Road Runner's MotorDirectionDebugger
  2 wheels   per-wheel ramp + fixed-power runs, velocity = kv * (power - ks)
  3 imu      gyro drift at rest; hub mounting checked from pitch/roll
  4 spin     N full turns against a floor line: IMU scale and encoder ticks
             per degree against a known angle (Pedro's turn tuner, with the
             true angle as the reference instead of the IMU)
  5 ramp     Road Runner's AngularRampLogger: static-friction power and
             deg/s per power when turning on the floor
  6/7 push   Road Runner's Forward/LateralPushTest: ticks per cm, slip included
  8 drift    the turning left when driving straight, cancelled by feedforward
  9/10       closed-loop squares on odometry, checked against a tape measure
  11 shooter  per speed, a distance proven by 5 singles + a 5-ball burst
"""

from ftc.hardware import DcMotor, DcMotorEx, DcMotorSimple, DistanceSensor
from ftc.navigation import AngleUnit
from ftc.opmode import LinearOpMode, TeleOp
from ftc.util import ElapsedTime
from drive import OmniDrive
from drive_cal import DriveCal
from jam import JamGuard
from shooter import Flywheel, RangeFinder
from shooter_cal import ShooterCal


@TeleOp(name="Calibration", group="pyftc")
class Calibration(LinearOpMode):
    # The first 8 are the drive calibration and are saved in DriveCal; 9 and 10
    # are tests that save nothing; 11 saves to ShooterCal.
    STEP_KEYS: list[str] = ["motors", "wheels", "imu", "spin", "ramp", "fwd", "strafe", "drift", "verify",
                            "square", "shooter"]
    STEP_TITLES: list[str] = ["Motor check", "Wheel matching", "IMU at rest", "Spin 5 turns", "Turn ramp",
                              "Forward push", "Strafe push", "Drift", "Verify: 60 cm square", "Test: 1 m square",
                              "Shooter distance"]
    STEP_WHERE: list[str] = ["ON BLOCKS", "ON BLOCKS", "floor, still", "floor, 1 m circle", "floor, 1 m circle",
                             "floor, by hand", "floor, by hand", "floor, 1.5 m clear", "floor, 1 m square",
                             "floor, 1.5 m square", "at the goal wall"]
    SPIN_TURNS: int = 5
    WHEEL_LEVELS: list[float] = [0.4, 0.6, 0.8, 1.0]
    FEED_POWER: float = 1.0
    # One ball is loaded per single shot and the feed simply runs this long:
    # stopping on the flywheel's dip missed shots on the robot.
    SINGLE_FEED_MS: float = 2000.0
    # The burst feeds like Main (only while the flywheel is at >= 90% of its
    # settled speed) for this long, enough for 5 balls with recovery.
    BURST_FEED_MS: float = 6000.0
    FEED_GATE: float = 0.9
    STREAK_NEEDED: int = 5
    BURST_BALLS: int = 5
    # Moving farther than this from where a streak started restarts it: the
    # streak proves one distance.
    MOVE_TOLERANCE_CM: float = 5.0
    SHOOTER_MAX_TPS: float = 2400.0

    cal: DriveCal
    drive: OmniDrive
    selected: int
    last_result: str
    push_cm: float

    collector: DcMotorEx
    shooter: DcMotorEx
    flywheel: Flywheel
    range_finder: RangeFinder
    shot_cal: ShooterCal
    feed_guard: JamGuard
    # Shooter step settings, kept between runs of the step.
    sh_row: int
    sh_vmin: float
    sh_vmax: float
    sh_vstep: float
    sh_fresh: bool

    def runOpMode(self) -> None:
        self.cal = DriveCal()
        self.cal.load()
        self.drive = OmniDrive(self.hardwareMap, self.cal)
        self.drive.init_imu()
        self.push_cm = 120.0
        self.collector = self.hardwareMap.get(DcMotorEx, "Collector")
        self.shooter = self.hardwareMap.get(DcMotorEx, "shooter")
        self.flywheel = Flywheel(self.shooter)
        self.range_finder = RangeFinder(self.hardwareMap.tryGet(DistanceSensor, RangeFinder.NAME))
        self.shot_cal = ShooterCal()
        self.shot_cal.load()
        self.feed_guard = JamGuard("shooter intake", self.collector)
        self.sh_row = 0
        self.sh_vmin = 1700.0
        self.sh_vmax = 2200.0
        self.sh_vstep = 100.0
        self.sh_fresh = False
        self.last_result = ""
        if self.cal.load_error != "":
            self.last_result = self.cal.load_error
        self.selected = self.first_undone()

        self.telemetry.addLine("Drive calibration. Press START for the menu.")
        self.telemetry.addLine("Steps 1-2 need the robot ON BLOCKS (wheels in the air).")
        self.telemetry.addLine(f"Saved steps on this hub: {self.cal.done_count()} of 8")
        self.telemetry.update()
        self.waitForStart()

        self.drive.start()
        self.gamepad1.resetEdgeDetection()
        while self.opModeIsActive():
            if self.gamepad1.dpadUpWasPressed():
                self.selected = (self.selected + len(self.STEP_KEYS) - 1) % len(self.STEP_KEYS)
            if self.gamepad1.dpadDownWasPressed():
                self.selected = (self.selected + 1) % len(self.STEP_KEYS)
            if self.gamepad1.aWasPressed():
                self.run_step(self.selected)
                self.gamepad1.resetEdgeDetection()
            if self.gamepad1.xWasPressed():
                self.erase()
                self.gamepad1.resetEdgeDetection()
            self.show_menu()
        self.drive.stop()

    # ------------------------------------------------------------------ menu

    def first_undone(self) -> int:
        for i in range(8):
            if not self.cal.has(self.STEP_KEYS[i]):
                return i
        return 8

    def show_menu(self) -> None:
        self.telemetry.addLine(f"CALIBRATION  saved {self.cal.done_count()} of 8")
        self.telemetry.addLine("dpad: choose   cross/A: run   X: erase drive numbers")
        for i in range(len(self.STEP_KEYS)):
            cursor = ">" if i == self.selected else " "
            mark = "[x]" if self.cal.has(self.STEP_KEYS[i]) else "[ ]"
            extra = ""
            if i >= 8:
                mark = "   "
            if self.STEP_KEYS[i] == "shooter":
                extra = f"  {self.shot_cal.count()} speeds saved"
            self.telemetry.addLine(f"{cursor} {mark} {i + 1}. {self.STEP_TITLES[i]}  ({self.STEP_WHERE[i]}){extra}")
        if self.last_result != "":
            self.telemetry.addLine("")
            self.telemetry.addLine(self.last_result)
        self.telemetry.update()

    def run_step(self, i: int) -> None:
        self.drive.use_corrections = True
        self.drive.set_float(False)
        self.drive.stop()
        key = self.STEP_KEYS[i]
        if key == "motors":
            self.step_motors()
        elif key == "wheels":
            self.step_wheels()
        elif key == "imu":
            self.step_imu()
        elif key == "spin":
            self.step_spin()
        elif key == "ramp":
            self.step_ramp()
        elif key == "fwd":
            self.step_push("fwd")
        elif key == "strafe":
            self.step_push("strafe")
        elif key == "drift":
            self.step_drift()
        elif key == "verify":
            self.step_square("9. Verify: 60 cm square", 60.0, "1 m x 1 m")
        elif key == "square":
            self.step_square("10. Test: 1 m square", 100.0, "1.5 m x 1.5 m")
        else:
            self.step_shooter()
        # Whatever a step did (or if STOP came mid-step), leave the drive safe.
        self.drive.stop()
        self.drive.set_float(False)
        self.drive.use_corrections = True
        self.drive.v_common = self.drive.common_speed()
        self.drive.start()
        if self.cal.has(key) and self.selected == i:
            self.selected = self.first_undone()

    def erase(self) -> None:
        if not self.ask("Erase drive calibration?", "Deletes every saved drive number on this hub\n(the shooter table stays).\nX (again) or cross/A: erase    B: keep"):
            return
        self.cal.wipe()
        self.drive.init_imu()
        self.last_result = "Calibration erased. The robot drives uncorrected until recalibrated."
        self.selected = 0

    # ------------------------------------------------------------------ helpers

    def show(self, title: str, body: str) -> None:
        self.telemetry.addLine(title)
        self.telemetry.addLine("")
        for line in body.split("\n"):
            self.telemetry.addLine(line)
        self.telemetry.update()

    def ask(self, title: str, body: str) -> bool:
        """Show a page; True for cross/A (or X), False for B or STOP."""
        self.drive.stop()
        self.gamepad1.resetEdgeDetection()
        while self.opModeIsActive():
            self.drive.update()
            self.show(title, body)
            if self.gamepad1.aWasPressed() or self.gamepad1.xWasPressed():
                return True
            if self.gamepad1.bWasPressed():
                return False
        return False

    def fail(self, title: str, body: str) -> None:
        self.drive.stop()
        self.last_result = title + ": not saved"
        self.ask(title, body + "\n\ncross/A: back to menu")

    def hold(self, ms: float) -> None:
        """Wait while keeping heading tracking alive (a plain sleep would miss
        the IMU wrapping past 180 degrees while the robot is still turning)."""
        t = ElapsedTime()
        while self.opModeIsActive() and t.milliseconds() < ms:
            self.drive.update()
            self.idle()

    def save(self, key: str, summary: str) -> None:
        self.cal.mark(key)
        try:
            self.cal.save()
        except RuntimeError as e:
            self.fail("Could not save", "Writing the calibration file failed:\n" + str(e))
            return
        # Read it back: a save that didn't reach the disk would otherwise only
        # show up as an uncalibrated robot at the next match.
        check = DriveCal()
        check.load()
        if not check.has(key):
            self.fail("Could not save", "The file on the hub does not contain this step after saving.")
            return
        self.last_result = self.STEP_TITLES[self.STEP_KEYS.index(key)] + " saved. " + summary

    def rot_ticks(self) -> float:
        return self.drive.combine(self.drive.ROT, self.drive.positions())

    def sign(self, x: float) -> float:
        if x < 0:
            return -1.0
        return 1.0

    # ------------------------------------------------------------------ 1. motors

    def step_motors(self) -> None:
        if not self.ask("1. Motor check  (ON BLOCKS)",
                        "Put the robot ON BLOCKS: all four wheels in the air.\n"
                        "Each wheel spins alone in BOTH directions. Watch\n"
                        "which wheel moves and whether it reverses.\n\n"
                        "cross/A: start    B: back"):
            return
        signs: list[float] = [1.0, 1.0, 1.0, 1.0]
        notes = ""
        for i in range(4):
            name = self.drive.WHEEL_NAMES[i]
            long_name = self.drive.WHEEL_LONG[i]
            before = self.drive.raw_position(i)
            self.drive.set_raw(i, 0.35 * self.drive.FWD[i])
            self.hold(1000)
            self.drive.set_raw(i, 0.0)
            self.hold(400)
            moved = self.drive.raw_position(i) - before
            counted = f"{moved:.0f} ticks"
            if abs(moved) < 100:
                counted = counted + "  (TOO FEW - encoder not counting?)"
            if not self.ask(f"1. Wheel {name}",
                            f"Did the {long_name.upper()} wheel spin,\n"
                            "the way that would push the robot FORWARD?\n"
                            f"Encoder: {counted}\n\n"
                            "cross/A: yes    B: no"):
                self.fail("Motor check failed",
                          f"{long_name} ({name}) is not right.\n"
                          "A different wheel spun: the motor names in the hub's\n"
                          "configuration are swapped - fix them there.\n"
                          "Right wheel, wrong way: flip its setDirection in drive.py.\n"
                          "Then run this step again.")
                return
            if abs(moved) < 100:
                self.fail("Encoder not counting",
                          f"{long_name} ({name}) turned but its encoder barely counted.\n"
                          "Check the encoder cable at the motor and at the hub port.")
                return
            reverse_before = self.drive.raw_position(i)
            self.drive.set_raw(i, -0.35 * self.drive.FWD[i])
            self.hold(1000)
            self.drive.set_raw(i, 0.0)
            self.hold(400)
            reverse_moved = self.drive.raw_position(i) - reverse_before
            if not self.ask(f"1. Wheel {name} reverse",
                            f"Did the same {long_name.upper()} wheel spin\n"
                            "the OPPOSITE way, as if driving BACKWARD?\n"
                            f"Encoder: {reverse_moved:.0f} ticks\n\n"
                            "cross/A: yes    B: no"):
                self.fail("Motor reverse check failed",
                          f"{long_name} ({name}) did not reverse correctly.\n"
                          "Check the motor and its wiring before calibrating.\n"
                          "The drive needs both directions for strafe.")
                return
            if abs(reverse_moved) < 100 or moved * reverse_moved >= 0:
                self.fail("Encoder reverse check failed",
                          f"{long_name} ({name}) did not count in both directions.\n"
                          "Check the motor and encoder wiring before calibrating.")
                return
            # The SDK already flips the encoder with setDirection; a remaining
            # mismatch is a wiring oddity, compensated rather than failed.
            signs[i] = self.sign(moved * self.drive.FWD[i])
            if signs[i] < 0:
                notes = notes + f" {name} encoder counts backwards (compensated)."
        self.cal.enc_sign = signs
        self.save("motors", "All four wheels OK." + notes)

    # ------------------------------------------------------------------ 2. wheels

    def step_wheels(self) -> None:
        if not self.ask("2. Wheel matching  (ON BLOCKS)",
                        "Robot ON BLOCKS, wheels in the air.\n"
                        "All wheels ramp up slowly, then run at 4 speeds,\n"
                        "first forward, then backward (about 15 s).\n"
                        "Finds how much power each wheel needs to start\n"
                        "and how fast it turns, so all four can be matched.\n\n"
                        "cross/A: start    B: back"):
            return
        ks_pos: list[float] = [0.0, 0.0, 0.0, 0.0]
        ks_neg: list[float] = [0.0, 0.0, 0.0, 0.0]
        kv_pos: list[float] = [0.0, 0.0, 0.0, 0.0]
        kv_neg: list[float] = [0.0, 0.0, 0.0, 0.0]
        for d in [1.0, -1.0]:
            ks: list[float] = [-1.0, -1.0, -1.0, -1.0]
            t = ElapsedTime()
            while self.opModeIsActive() and t.milliseconds() < 3000:
                p = 0.3 * t.milliseconds() / 3000.0
                for i in range(4):
                    self.drive.set_raw(i, d * p)
                for i in range(4):
                    if ks[i] < 0 and self.drive.velocity(i) * d > 40.0:
                        ks[i] = p
                self.show("2. Wheel matching", f"ramping {'forward' if d > 0 else 'backward'}: power {p:.2f}")
            for i in range(4):
                if ks[i] < 0:
                    ks[i] = 0.3
            num: list[float] = [0.0, 0.0, 0.0, 0.0]
            den: list[float] = [0.0, 0.0, 0.0, 0.0]
            for level in self.WHEEL_LEVELS:
                for i in range(4):
                    self.drive.set_raw(i, d * level)
                self.show("2. Wheel matching", f"{'forward' if d > 0 else 'backward'} at power {level:.1f}")
                self.hold(700)
                total: list[float] = [0.0, 0.0, 0.0, 0.0]
                n = 0
                t.reset()
                while self.opModeIsActive() and t.milliseconds() < 300:
                    for i in range(4):
                        total[i] = total[i] + self.drive.velocity(i) * d
                    n = n + 1
                for i in range(4):
                    x = level - ks[i]
                    num[i] = num[i] + total[i] / max(n, 1) * x
                    den[i] = den[i] + x * x
            self.drive.stop()
            self.hold(1000)
            for i in range(4):
                kv = num[i] / den[i] if den[i] > 0 else 0.0
                if d > 0:
                    ks_pos[i] = ks[i]
                    kv_pos[i] = kv
                else:
                    ks_neg[i] = ks[i]
                    kv_neg[i] = kv
        if not self.opModeIsActive():
            return

        top = 0.0
        for i in range(4):
            if kv_pos[i] <= 0 or kv_neg[i] <= 0:
                self.fail("Wheel matching failed",
                          f"{self.drive.WHEEL_NAMES[i]} turned the wrong way or its encoder\n"
                          "did not count. Run step 1 (Motor check) first.")
                return
            top = max(top, kv_pos[i] * (1.0 - ks_pos[i]), kv_neg[i] * (1.0 - ks_neg[i]))
        report = "wheel  start power +/-   top speed +/- (% of best)\n"
        weakest = 100.0
        for i in range(4):
            fp = 100.0 * kv_pos[i] * (1.0 - ks_pos[i]) / top
            fn = 100.0 * kv_neg[i] * (1.0 - ks_neg[i]) / top
            weakest = min(weakest, fp, fn)
            report = report + f"{self.drive.WHEEL_NAMES[i]}   {ks_pos[i]:.2f} / {ks_neg[i]:.2f}   {fp:.0f}% / {fn:.0f}%\n"
        if weakest < 85.0:
            report = report + "\nOne wheel is much weaker: look for rubbing, a tight\nbearing or a bad gearbox before relying on matching.\n"
        report = report + f"\nFull stick will be {weakest:.0f}% of the best wheel's top speed\nso every wheel can keep up.\n\ncross/A: save    B: discard"
        if not self.ask("2. Wheel matching results", report):
            self.last_result = "Wheel matching discarded."
            return
        self.cal.ks_pos = ks_pos
        self.cal.ks_neg = ks_neg
        self.cal.kv_pos = kv_pos
        self.cal.kv_neg = kv_neg
        self.save("wheels", f"Weakest wheel {weakest:.0f}%.")

    # ------------------------------------------------------------------ 3. imu

    def pitch_roll_error(self) -> float:
        ypr = self.drive.imu.getRobotYawPitchRollAngles()
        return abs(ypr.getPitch(AngleUnit.DEGREES)) + abs(ypr.getRoll(AngleUnit.DEGREES))

    def step_imu(self) -> None:
        if not self.ask("3. IMU at rest  (floor)",
                        "Robot on the floor, on its wheels, nobody touching it.\n"
                        "For 5 s the gyro's drift is measured, and pitch/roll\n"
                        "check that the hub's mounting is set right.\n\n"
                        "cross/A: start    B: back"):
            return
        self.drive.start()
        self.hold(300)
        y0 = self.drive.unwrapped_yaw
        t = ElapsedTime()
        tilt = 0.0
        n = 0
        while self.opModeIsActive() and t.milliseconds() < 5000:
            self.drive.update()
            tilt = tilt + self.pitch_roll_error()
            n = n + 1
            self.show("3. IMU at rest", f"measuring... {5.0 - t.seconds():.1f} s   don't touch the robot")
        drift = (self.drive.unwrapped_yaw - y0) / t.seconds()
        tilt = tilt / max(n, 1)
        report = f"Drift at rest: {drift:.3f} deg/s ({drift * 150.0:.1f} deg over a 2:30 match)\n"
        if abs(drift) > 0.1:
            report = report + "That is high: redo this with the robot really still.\n"
        logo = self.cal.imu_logo
        usb = self.cal.imu_usb
        if tilt < 8.0:
            report = report + f"Hub mounting OK (logo {logo}, USB {usb}): pitch+roll {tilt:.1f} deg.\n"
        else:
            # Pitch and roll say which way is up; only the logo direction matters
            # for heading (the USB direction only rotates yaw by a constant that
            # resetYaw removes), so try the six logo directions.
            best = 1.0e9
            for candidate in ["UP", "DOWN", "FORWARD", "BACKWARD", "LEFT", "RIGHT"]:
                cand_usb = "UP"
                if candidate == "UP" or candidate == "DOWN":
                    cand_usb = "FORWARD"
                self.drive.init_imu_as(candidate, cand_usb)
                self.hold(250)
                err = self.pitch_roll_error()
                if err < best:
                    best = err
                    logo = candidate
                    usb = cand_usb
            self.drive.init_imu_as(logo, usb)
            if best < 8.0:
                report = report + f"Mounting was WRONG (pitch+roll {tilt:.0f} deg).\nFound: logo {logo}, USB {usb} (pitch+roll {best:.1f} deg).\n"
            else:
                report = report + f"Hub is not mounted square to the robot (best fit\nstill {best:.0f} deg off). Heading will be unreliable.\n"
        if not self.ask("3. IMU results", report + "\ncross/A: save    B: discard"):
            self.drive.init_imu()
            self.last_result = "IMU step discarded."
            return
        self.cal.imu_drift = drift
        self.cal.imu_logo = logo
        self.cal.imu_usb = usb
        self.save("imu", f"Drift {drift:.3f} deg/s, logo {logo}.")

    # ------------------------------------------------------------------ 4. spin

    def step_spin(self) -> None:
        if not self.ask("4. Spin 5 turns  (floor)",
                        "Floor, 1 m circle of free space.\n"
                        "Line up one straight edge of the robot EXACTLY with a\n"
                        "tile seam or a tape line and remember which edge.\n"
                        "The robot spins 5 turns by itself; then you line the\n"
                        "same edge up again. 5 turns = 1800 deg exactly, which\n"
                        "shows the IMU's error and the encoder ticks per degree.\n\n"
                        "cross/A: start    B: back"):
            return
        self.drive.use_corrections = False
        self.drive.start()
        r0 = self.rot_ticks()
        target = self.SPIN_TURNS * 360.0 - 30.0
        t = ElapsedTime()
        while self.opModeIsActive() and abs(self.drive.unwrapped_yaw) < target and t.seconds() < 30.0:
            self.drive.update()
            self.drive.drive(0.0, 0.0, 0.35)
            self.show("4. Spinning", f"IMU: {self.drive.unwrapped_yaw:.0f} deg")
        self.drive.stop()
        self.hold(600)
        if abs(self.drive.unwrapped_yaw) < target:
            self.fail("Spin failed", f"The IMU saw only {self.drive.unwrapped_yaw:.0f} deg in 30 s.\nIs the robot stuck, or the IMU not working?")
            return
        self.gamepad1.resetEdgeDetection()
        while self.opModeIsActive():
            self.drive.update()
            self.drive.drive(0.0, 0.0, -0.25 * self.gamepad1.right_stick_x)
            self.show("4. Line it up again",
                      "Turn with gamepad1 RIGHT STICK X (slow) until the same\n"
                      "edge is exactly on the line again.\n"
                      f"IMU so far: {self.drive.unwrapped_yaw:.1f} deg\n\n"
                      "cross/A: lined up    B: cancel")
            if self.gamepad1.aWasPressed():
                break
            if self.gamepad1.bWasPressed():
                self.last_result = "Spin cancelled."
                return
        self.drive.stop()
        self.hold(400)
        imu_total = self.drive.unwrapped_yaw
        turns = round(abs(imu_total) / 360.0)
        if turns != self.SPIN_TURNS:
            self.fail("Spin failed", f"IMU total {imu_total:.0f} deg is not close to {self.SPIN_TURNS} turns.\nLine up the same edge as at the start and try again.")
            return
        true_deg = turns * 360.0 * self.sign(imu_total)
        scale = true_deg / imu_total
        ticks_per_deg = (self.rot_ticks() - r0) / true_deg
        if scale < 0.9 or scale > 1.1:
            self.fail("Spin failed", f"IMU error {100.0 * (scale - 1.0):.1f}% is not believable.\nSomething moved the robot, or the edge was lined up a turn off.")
            return
        report = (f"IMU read {imu_total:.1f} deg for {true_deg:.0f} deg\n"
                  f"-> scale {scale:.4f} ({100.0 * (scale - 1.0):+.2f}%)\n"
                  f"Encoders: {ticks_per_deg:.3f} ticks per degree of turn\n\n"
                  "cross/A: save    B: discard")
        if not self.ask("4. Spin results", report):
            self.last_result = "Spin discarded."
            return
        self.cal.imu_scale = scale
        self.cal.ticks_per_deg = ticks_per_deg
        self.save("spin", f"IMU scale {scale:.4f}.")

    # ------------------------------------------------------------------ 5. ramp

    def step_ramp(self) -> None:
        if not self.ask("5. Turn ramp  (floor)",
                        "Floor, 1 m circle of free space.\n"
                        "The robot turns in place, speeding up slowly for 6 s.\n"
                        "Measures the power it needs to start moving, and how\n"
                        "fast it turns per power (used by heading hold).\n\n"
                        "cross/A: start    B: back"):
            return
        self.drive.use_corrections = False
        self.drive.start()
        powers: list[float] = []
        rates: list[float] = []
        ks = -1.0
        above = 0
        t = ElapsedTime()
        while self.opModeIsActive() and t.milliseconds() < 6000 and abs(self.drive.heading()) < 1080.0:
            p = 0.6 * t.milliseconds() / 6000.0
            self.drive.update()
            self.drive.drive(0.0, 0.0, p)
            w = self.drive.yaw_rate()
            if ks < 0:
                if abs(w) > 8.0:
                    above = above + 1
                    if above >= 3:
                        ks = p
                else:
                    above = 0
            else:
                powers.append(p)
                rates.append(w)
            self.show("5. Turn ramp", f"power {p:.2f}   {w:.0f} deg/s")
        self.drive.stop()
        self.hold(800)
        if ks < 0:
            self.fail("Turn ramp failed", "The robot never started turning (up to power 0.6).\nIs it stuck or are the wheels off the floor?")
            return
        num = 0.0
        den = 0.0
        used = 0
        for k in range(len(powers)):
            x = powers[k] - ks
            if x > 0.05:
                num = num + rates[k] * x
                den = den + x * x
                used = used + 1
        if used < 10:
            self.fail("Turn ramp failed", "Too few samples above the starting power.\nMake sure the robot can turn freely and try again.")
            return
        kv = num / den
        way = "counter-clockwise" if kv > 0 else "clockwise"
        if not self.ask("5. Turn ramp results",
                        f"Starts turning at power {ks:.3f}\n"
                        f"{abs(kv):.0f} deg/s per unit of power above that\n"
                        f"(+turn stick turns the robot {way} seen from above)\n\n"
                        "cross/A: save    B: discard"):
            self.last_result = "Turn ramp discarded."
            return
        self.cal.turn_ks = ks
        self.cal.turn_kv = kv
        self.save("ramp", f"Start power {ks:.3f}, {abs(kv):.0f} deg/s per power.")

    # ------------------------------------------------------------------ 6/7. push

    def step_push(self, key: str) -> None:
        forward = key == "fwd"
        way = "FORWARD" if forward else "to the RIGHT (sideways)"
        title = "6. Forward push" if forward else "7. Strafe push"
        self.gamepad1.resetEdgeDetection()
        while self.opModeIsActive():
            if self.gamepad1.dpadUpWasPressed():
                self.push_cm = min(400.0, self.push_cm + 10.0)
            if self.gamepad1.dpadDownWasPressed():
                self.push_cm = max(30.0, self.push_cm - 10.0)
            self.drive.update()
            self.show(title + "  (floor, by hand)",
                      "The motors go limp and you push the robot by hand\n"
                      f"{way} over a distance you have measured.\n"
                      "Mark where it starts (e.g. an edge on a tape line).\n\n"
                      f"Distance you will push: {self.push_cm:.0f} cm  (dpad up/down)\n\n"
                      "cross/A: start    B: back")
            if self.gamepad1.aWasPressed():
                break
            if self.gamepad1.bWasPressed():
                return
        self.drive.stop()
        self.drive.set_float(True)
        self.drive.start()
        p0 = self.drive.positions()
        main_t = 0.0
        cross_t = 0.0
        self.gamepad1.resetEdgeDetection()
        while self.opModeIsActive():
            self.drive.update()
            pos = self.drive.positions()
            delta: list[float] = []
            for i in range(4):
                delta.append(pos[i] - p0[i])
            fwd_t = self.drive.combine(self.drive.FWD, delta)
            str_t = self.drive.combine(self.drive.STR, delta)
            main_t = fwd_t if forward else str_t
            cross_t = str_t if forward else fwd_t
            old = self.cal.ticks_per_cm_fwd if forward else self.cal.ticks_per_cm_str
            self.show(title,
                      f"Push {way} exactly {self.push_cm:.0f} cm.\n"
                      "Keep it square: don't let it turn.\n\n"
                      f"encoders: {main_t:.0f} ticks (~{main_t / old:.1f} cm by the old number)\n"
                      f"turned: {self.drive.heading():.1f} deg\n\n"
                      "cross/A: I'm at the mark    B: cancel")
            if self.gamepad1.aWasPressed():
                break
            if self.gamepad1.bWasPressed():
                self.drive.set_float(False)
                self.last_result = title + " cancelled."
                return
        self.drive.set_float(False)
        if abs(main_t) < 50.0:
            self.fail(title + " failed", "The encoders barely counted. Push further,\nor check step 1 (Motor check).")
            return
        ticks_per_cm = main_t / self.push_cm
        report = f"{main_t:.0f} ticks over {self.push_cm:.0f} cm -> {ticks_per_cm:.3f} ticks/cm\n"
        if ticks_per_cm < 0:
            report = report + "(negative: the encoders count this way backwards;\nthat is fine, the sign is kept)\n"
        if abs(self.drive.heading()) > 3.0:
            report = report + f"It turned {self.drive.heading():.1f} deg while pushed: redo for a better number.\n"
        if abs(cross_t) > 0.1 * abs(main_t):
            report = report + f"Wheels also counted {100.0 * abs(cross_t / main_t):.0f}% sideways: push straighter.\n"
        if not self.ask(title + " results", report + "\ncross/A: save    B: discard"):
            self.last_result = title + " discarded."
            return
        if forward:
            self.cal.ticks_per_cm_fwd = ticks_per_cm
        else:
            self.cal.ticks_per_cm_str = ticks_per_cm
        self.save(key, f"{ticks_per_cm:.3f} ticks/cm.")

    # ------------------------------------------------------------------ 8. drift

    def step_drift(self) -> None:
        if not self.cal.has("ramp"):
            self.fail("Do step 5 first", "Drift is measured in degrees per second and turned\ninto a power with the Turn ramp result.")
            return
        if not self.ask("8. Drift  (floor)",
                        "Floor, 1.5 m clear to the front, back, left and right.\n"
                        "The robot drives forward, back, right and left at half\n"
                        "power (about 1.5 s each, ends near where it started)\n"
                        "and measures how much it turns by itself.\n\n"
                        "cross/A: start    B: back"):
            return
        old_fwd = self.cal.drift_fwd
        old_str = self.cal.drift_str
        self.cal.drift_fwd = 0.0
        self.cal.drift_str = 0.0
        self.drive.start()
        fwd_cmd: list[float] = [0.5, -0.5, 0.0, 0.0]
        str_cmd: list[float] = [0.0, 0.0, 0.5, -0.5]
        needed: list[float] = [0.0, 0.0, 0.0, 0.0]
        rates: list[float] = [0.0, 0.0, 0.0, 0.0]
        for k in range(4):
            t = ElapsedTime()
            total = 0.0
            n = 0
            while self.opModeIsActive() and t.milliseconds() < 1500:
                self.drive.update()
                self.drive.drive(fwd_cmd[k], str_cmd[k], 0.0)
                if t.milliseconds() > 500:
                    total = total + self.drive.yaw_rate()
                    n = n + 1
                self.show("8. Drift", f"move {k + 1} of 4")
            self.drive.stop()
            self.hold(800)
            rates[k] = total / max(n, 1)
            needed[k] = -rates[k] / self.cal.turn_kv
        self.cal.drift_fwd = old_fwd
        self.cal.drift_str = old_str
        if not self.opModeIsActive():
            return
        drift_fwd = (needed[0] / 0.5 + needed[1] / -0.5) / 2.0
        drift_str = (needed[2] / 0.5 + needed[3] / -0.5) / 2.0
        if not self.ask("8. Drift results",
                        "Turning by itself while driving straight:\n"
                        f"forward {rates[0]:+.1f}  back {rates[1]:+.1f}  right {rates[2]:+.1f}  left {rates[3]:+.1f} deg/s\n"
                        f"-> correction {drift_fwd:+.3f} (forward), {drift_str:+.3f} (strafe)\n"
                        "Heading hold catches what is left.\n\n"
                        "cross/A: save    B: discard"):
            self.last_result = "Drift discarded."
            return
        self.cal.drift_fwd = drift_fwd
        self.cal.drift_str = drift_str
        self.save("drift", f"Corrections {drift_fwd:+.3f} / {drift_str:+.3f}.")


    # ------------------------------------------------------------------ 9/10. squares

    def step_square(self, title: str, side: float, room: str) -> None:
        if not self.ask(title + "  (floor)",
                        f"Floor, {room} clear. Mark the robot's position and\n"
                        f"the way it faces. It drives forward {side:.0f}, right {side:.0f},\n"
                        f"back {side:.0f}, left {side:.0f} cm without turning, then turns\n"
                        "back to its heading. Measure how far it is from the mark.\n\n"
                        "cross/A: start    B: back"):
            return
        # 0.5 power covers ~25 cm/s at worst; a leg that takes longer is stuck.
        timeout = 3.0 + side / 25.0
        self.drive.start()
        ok = self.drive.drive_cm(self, side, 0.0, 0.5, timeout)
        self.hold(300)
        ok = self.drive.drive_cm(self, 0.0, -side, 0.5, timeout) and ok
        self.hold(300)
        ok = self.drive.drive_cm(self, -side, 0.0, 0.5, timeout) and ok
        self.hold(300)
        ok = self.drive.drive_cm(self, 0.0, side, 0.5, timeout) and ok
        self.hold(300)
        ok = self.drive.turn_to(self, 0.0, 0.4, 4.0) and ok
        self.hold(500)
        note = "" if ok else "A move timed out (see below).\n"
        self.last_result = f"{side:.0f} cm square: ended at {self.drive.x_cm:+.1f} / {-self.drive.y_cm:+.1f} cm, {self.drive.heading():+.1f} deg by odometry."
        self.ask(title + " results",
                 note +
                 "Where the robot THINKS it ended, from the start mark:\n"
                 f"  {self.drive.x_cm:+.1f} cm forward, {-self.drive.y_cm:+.1f} cm right, {self.drive.heading():+.1f} deg\n\n"
                 "Now measure where it REALLY is:\n"
                 "  within ~3 cm and ~2 deg: good\n"
                 "  off along one direction: redo 6 or 7 (push)\n"
                 "  turned: redo 4 (spin) and 8 (drift)\n"
                 "  odometry far from reality: wheels slipped, drive slower\n\n"
                 "cross/A: back to menu")

    # ------------------------------------------------------------------ 11. shooter

    def shooter_speeds(self) -> list[float]:
        out: list[float] = []
        v = self.sh_vmin
        while v <= self.sh_vmax + 0.5:
            out.append(v)
            v = v + self.sh_vstep
        # The top speed is about what Main's fresh battery reaches: always test it.
        if out[len(out) - 1] < self.sh_vmax - 0.5:
            out.append(self.sh_vmax)
        return out

    def shooter_setup(self) -> bool:
        """The settings page. True to start, False for back or STOP."""
        rows = 4
        self.gamepad1.resetEdgeDetection()
        self.range_finder.clear()
        while self.opModeIsActive():
            if self.gamepad1.dpadUpWasPressed():
                self.sh_row = (self.sh_row + rows - 1) % rows
            if self.gamepad1.dpadDownWasPressed():
                self.sh_row = (self.sh_row + 1) % rows
            if self.gamepad1.dpadRightWasPressed():
                self.shooter_adjust(1.0)
            if self.gamepad1.dpadLeftWasPressed():
                self.shooter_adjust(-1.0)
            self.drive.update()
            self.range_finder.update()
            speeds = self.shooter_speeds()
            lines = ["For each speed you drive the robot (left stick move,",
                     "right stick turn) to where you think it scores and fire",
                     "ONE ball at a time. 5 in a row from one spot, then a",
                     "5-ball burst all in, saves that spot's distance.",
                     "",
                     "Distance now: " + self.range_finder.describe()]
            labels = [f"slowest       {self.sh_vmin:.0f} t/s",
                      f"fastest       {self.sh_vmax:.0f} t/s",
                      f"speed step    {self.sh_vstep:.0f} t/s",
                      "saved speeds  " + (f"START FRESH (drop {self.shot_cal.count()})" if self.sh_fresh else f"keep {self.shot_cal.count()}")]
            for k in range(rows):
                cursor = ">" if k == self.sh_row else " "
                lines.append(cursor + " " + labels[k])
            lines.append("")
            lines.append(f"{len(speeds)} speeds to test")
            lines.append("")
            lines.append("dpad: choose/change   cross/A: start   B: back")
            self.telemetry.addLine("11. Shooter distance  (at the goal wall)")
            for line in lines:
                self.telemetry.addLine(line)
            self.telemetry.update()
            if self.gamepad1.aWasPressed():
                return True
            if self.gamepad1.bWasPressed():
                return False
        return False

    def shooter_adjust(self, step: float) -> None:
        r = self.sh_row
        if r == 0:
            self.sh_vmin = min(self.sh_vmax, max(400.0, self.sh_vmin + 100.0 * step))
        elif r == 1:
            self.sh_vmax = min(self.SHOOTER_MAX_TPS, max(self.sh_vmin, self.sh_vmax + 100.0 * step))
        elif r == 2:
            self.sh_vstep = min(500.0, max(50.0, self.sh_vstep + 50.0 * step))
        else:
            self.sh_fresh = not self.sh_fresh

    def measure_cm(self, ms: float) -> float:
        """Median distance over ms with the robot still; -1 if no reading."""
        self.range_finder.clear()
        t = ElapsedTime()
        while self.opModeIsActive() and t.milliseconds() < ms:
            self.drive.update()
            self.flywheel.update()
            self.range_finder.update()
        return self.range_finder.cm()

    def feed_for(self, ms: float, gated: bool, what: str) -> None:
        """Run the shooter intake for ms. gated: only while the flywheel is at
        FEED_GATE of its settled speed, as Main's burst does."""
        self.drive.stop()
        self.feed_guard.rearm()
        t = ElapsedTime()
        while self.opModeIsActive() and t.milliseconds() < ms:
            self.drive.update()
            self.flywheel.update()
            feed = self.FEED_POWER
            if gated and self.flywheel.velocity < self.flywheel.prime * self.FEED_GATE:
                feed = 0.0
            self.feed_guard.update(feed)
            self.show("11. Shooter distance", f"{what}  {(ms - t.milliseconds()) / 1000.0:.1f} s   flywheel {self.flywheel.velocity:.0f} t/s")
        self.feed_guard.update(0.0)

    def ask_landed(self, title: str, body: str) -> int:
        """1 in, 2 missed, 3 not counted (no ball came out, bad load...)."""
        self.drive.stop()
        self.gamepad1.resetEdgeDetection()
        while self.opModeIsActive():
            self.drive.update()
            self.flywheel.update()
            self.show(title, body + "\n\ncross/A: IN    circle/B: missed\ntriangle/Y: don't count it")
            if self.gamepad1.aWasPressed():
                return 1
            if self.gamepad1.bWasPressed():
                return 2
            if self.gamepad1.yWasPressed():
                return 3
        return 3

    def step_shooter(self) -> None:
        if not self.range_finder.present:
            self.fail("No distance sensor",
                      f"The hub configuration has no '{RangeFinder.NAME}'.\n"
                      "Add it (REV 2M Distance Sensor, I2C port), save the\n"
                      "configuration, restart this OpMode.")
            return
        if not self.shooter_setup():
            return
        if self.sh_fresh:
            # Only in memory: the file is overwritten when the first speed is saved.
            self.shot_cal.reset()
            self.sh_fresh = False
        # Shooter intake direction, same as Main's MagDump.
        self.collector.setDirection(DcMotorSimple.Direction.FORWARD)
        self.collector.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
        self.drive.start()
        speeds = self.shooter_speeds()
        saved = 0
        k = 0
        while self.opModeIsActive() and k < len(speeds):
            r = self.shooter_speed(speeds, k)
            if r == 1:
                saved = saved + 1
                k = k + 1
            elif r == 2:
                k = k + 1
            elif r == 3:
                k = max(0, k - 1)
            else:
                break
        self.flywheel.off()
        self.feed_guard.update(0.0)
        self.collector.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.FLOAT)
        self.drive.stop()
        # Whatever was not saved (e.g. an unused "start fresh") goes back to the file.
        self.shot_cal = ShooterCal()
        self.shot_cal.load()
        self.last_result = f"Shooter: {saved} speeds saved this run; table has {self.shot_cal.count()}."

    def shooter_speed(self, speeds: list[float], k: int) -> int:
        """Driver-controlled search for one speed's distance. Returns 1 saved,
        2 next speed, 3 previous speed, 5 finish (share/back or STOP)."""
        v = speeds[k]
        self.flywheel.spin_velocity(v)
        self.range_finder.clear()
        streak = 0
        streak_cm: list[float] = []
        start_cm = -1.0
        note = ""
        self.gamepad1.resetEdgeDetection()
        while self.opModeIsActive():
            self.drive.update()
            self.flywheel.update()
            self.range_finder.update()
            self.drive.teleop_gamepad(self.gamepad1)
            self.show_speed_page(speeds, k, streak, start_cm, note)
            if self.gamepad1.dpadRightWasPressed():
                return 2
            if self.gamepad1.dpadLeftWasPressed():
                return 3
            if self.gamepad1.backWasPressed():
                return 5
            if not self.gamepad1.aWasPressed():
                continue
            if not self.flywheel.ready:
                note = "Wait for the flywheel to settle."
                continue
            self.drive.stop()
            cm = self.measure_cm(250.0)
            if cm < 0:
                note = "No distance reading: is the sensor facing the wall?"
                continue
            if streak > 0 and abs(cm - start_cm) > self.MOVE_TOLERANCE_CM:
                note = f"Moved {cm - start_cm:+.0f} cm: the streak restarts here."
                streak = 0
                streak_cm = []
            if streak == 0:
                start_cm = cm
            prime = self.flywheel.prime
            if streak < self.STREAK_NEEDED:
                self.feed_for(self.SINGLE_FEED_MS, False, "FIRING 1 ball")
                answer = self.ask_landed("11. Did it go in?", f"{v:.0f} t/s (settled {prime:.0f}), {cm:.1f} cm\nin a row so far: {streak}")
                if answer == 1:
                    streak = streak + 1
                    streak_cm.append(cm)
                    note = ""
                elif answer == 2:
                    streak = 0
                    streak_cm = []
                    note = "Missed: move if you want and try again."
                else:
                    note = "Not counted."
            else:
                self.feed_for(self.BURST_FEED_MS, True, f"BURST of {self.BURST_BALLS}")
                answer = self.ask_landed(f"11. All {self.BURST_BALLS} in?", f"{v:.0f} t/s (settled {prime:.0f}), {cm:.1f} cm")
                if answer == 1:
                    streak_cm.append(cm)
                    if self.save_speed(v, prime, RangeFinder.median(streak_cm)):
                        return 1
                    return 5
                if answer == 2:
                    streak = 0
                    streak_cm = []
                    note = "Burst missed: the streak restarts."
                else:
                    note = "Burst not counted: load 5 and fire again."
            self.gamepad1.resetEdgeDetection()
        return 5

    def show_speed_page(self, speeds: list[float], k: int, streak: int, start_cm: float, note: str) -> None:
        v = speeds[k]
        lines: list[str] = []
        state = f"settled {self.flywheel.prime:.0f} t/s ({self.flywheel.rpm(self.flywheel.prime):.0f} rpm)" if self.flywheel.ready else f"spinning up: {self.flywheel.velocity:.0f} t/s"
        lines.append(f"flywheel {state}")
        lines.append("distance " + self.range_finder.describe())
        old = self.shot_cal.index_of(v)
        if old >= 0:
            lines.append(f"saved for this speed: {self.shot_cal.point_cm[old]:.1f} cm (would be replaced)")
        lines.append("")
        if streak == 0:
            lines.append(f"Drive to a spot and fire. {self.STREAK_NEEDED} in a row needed.")
        elif streak < self.STREAK_NEEDED:
            lines.append(f"{streak} of {self.STREAK_NEEDED} in a row at {start_cm:.0f} cm. Stay within {self.MOVE_TOLERANCE_CM:.0f} cm.")
        else:
            lines.append(f"{self.STREAK_NEEDED} in a row! Load {self.BURST_BALLS} balls: next fire is the burst.")
        if note != "":
            lines.append(note)
        lines.append("")
        lines.append("left stick: move   right stick: turn")
        lines.append("cross/A: fire" + (" the burst" if streak >= self.STREAK_NEEDED else " 1 ball"))
        lines.append("dpad right/left: next/previous speed   share/back: finish")
        self.telemetry.addLine(f"11. Shooter  speed {k + 1} of {len(speeds)}: {v:.0f} t/s")
        for line in lines:
            self.telemetry.addLine(line)
        self.telemetry.update()

    def save_speed(self, target: float, tps: float, cm: float) -> bool:
        self.shot_cal.set_point(target, tps, cm)
        try:
            self.shot_cal.save()
        except RuntimeError as e:
            self.fail("Could not save", "Writing the shooter file failed:\n" + str(e))
            return False
        check = ShooterCal()
        check.load()
        if check.index_of(target) < 0:
            self.fail("Could not save", "The shooter file on the hub does not hold this speed after saving.")
            return False
        self.show("11. Saved", f"{target:.0f} t/s scores at {cm:.1f} cm.")
        self.hold(1500)
        return True
