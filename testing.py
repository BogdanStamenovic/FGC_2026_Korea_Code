"""Testing: check every part of the robot by hand, one at a time.

Two pages; share switches between them (switching stops everything that
moves; servos stay where they are). Gamepad 1 only.

DRIVE page (the old Drive Test): drives in one pure direction at a time, so
you can see whether "forward" really goes forward, "strafe right" really goes
right, and so on. Put the robot on the floor with room around it. The robot
only moves while a button is held; let go and it stops.
  dpad up / down        forward / backward
  dpad right / left     strafe right / left
  right / left bumper   turn right / left (on the spot)
  triangle / cross      power +0.1 / -0.1 (starts at 0.4)
  square                RAW <-> CALIBRATED

PARTS page: every motor and servo besides the wheels, in a list.
  dpad up / down        choose a part
  motors and continuous servos (only while a bumper is held):
    right / left bumper run it one way / the other; telemetry names both
                        ways as Main uses them (e.g. pickup / reverse)
    triangle / cross    power +0.1 / -0.1 (starts at 0.5, one power for all)
  servos:
    right / left bumper go to Main's two positions for it
    triangle / cross    nudge the position +0.02 / -0.02, to find a better
                        value: telemetry shows the exact number to copy into
                        main.py
Directions, run modes and positions are main.py's, so "pickup" here is
pickup in Main. The clutch refuses to deploy while the Collector turns
(Main's rule, it protects the clutch). To see it couple the Collector to the
shooter intake: clutch, right bumper (deployed); then Collector, right
bumper: the shooter intake should turn too.

DRIVE page details. RAW (the default) is the plain wheel mix and motor
directions from drive.py, nothing else: if RAW goes the wrong way, the mix
or a motor direction is wrong. CALIBRATED adds the Calibration OpMode's
corrections, exactly as Main drives (without heading hold): if RAW is right
but CALIBRATED is not, the calibration file is. Holding two direction
buttons at once does nothing.

Telemetry shows what each wheel was told and what its encoder says it did,
and how far the robot turned during the move (a pure move should stay near
0 degrees). After each move it also shows each wheel's average speed as a
percentage of the four wheels' average: a robot that curves has a slow wheel
on the inside of the curve, and this names it.

Motor current is shown too, live and averaged per move, to tell a weak
wheel's cause (HD Hex: ~8.5 A at stall):
  slow + MORE current than the others   something drags: gearbox, rollers,
                                        a rubbing chain or frame
  slow + about the SAME current         the motor or gearbox is worn/weak
  slow + LESS current                   power doesn't reach it: connector,
                                        cable, or the hub port
"""

from ftc.hardware import CRServo, DcMotor, DcMotorEx, DcMotorSimple, Gamepad, LynxModule, Servo, VoltageSensor
from ftc.navigation import CurrentUnit
from ftc.opmode import LinearOpMode, TeleOp
from ftc.util import ElapsedTime
from drive import OmniDrive
from drive_cal import DriveCal


@TeleOp(name="Testing", group="pyftc")
class Testing(LinearOpMode):
    POWER_STEP: float = 0.1
    # Wheel speeds are averaged from this long after a move starts: while the
    # robot accelerates, the wheels are not yet at their own speed.
    SETTLE_MS: float = 300.0
    # A wheel below this share of the average is called out as slow.
    SLOW_PERCENT: float = 92.0
    START_POWER: float = 0.4
    PART_START_POWER: float = 0.5
    SERVO_STEP: float = 0.02

    # Copies of main.py's values: change them there and here together.
    CHAIN_STOP_START: float = 0.7
    CHAIN_STOP_ENGAGED: float = 0.4
    CHAIN_DROP_START: float = 0.0
    CHAIN_DROP_FISHING: float = 0.25
    CLUTCH_NAME: str = "clutch"
    CLUTCH_DEPLOYED: float = 0.9
    CLUTCH_RETRACTED: float = 0.74
    CLUTCH_STOPPED_TPS: float = 20.0
    CLUTCH_STILL_MS: float = 100.0
    FIXATOR_POWER: float = 1.0
    CLIMBER_UP: float = 1.0
    CLIMB_POWER: float = -1.0
    SECOND_CLIMB_NAME: str = "SecondClimbUpper"
    SECOND_CLIMB_POWER: float = -1.0

    cal: DriveCal
    drive: OmniDrive
    hubs: list[LynxModule]
    parts_page: bool
    power: float
    raw: bool
    # The move being held ("" when stopped), and the heading when it began.
    move: str
    move_start_deg: float
    last_move: str
    last_turned: float
    move_clock: ElapsedTime
    speed_sum: list[float]
    speed_n: int
    last_speeds: str
    # Current per wheel: this loop, summed over the move, and peak in the move.
    amps: list[float]
    amps_sum: list[float]
    amps_peak: list[float]
    last_amps: str
    batteries: list[VoltageSensor]
    volts: float
    volts_low: float
    held: int

    # The PARTS page. Part i is part_kinds[i] ("motor", "crservo" or "servo")
    # number part_slot[i] in motors / crservos / servos. For motors and CR
    # servos, rb_value is the sign of the power the right bumper sends; for
    # servos, rb_value / lb_value are the two positions.
    collector: DcMotorEx
    motors: list[DcMotorEx]
    crservos: list[CRServo]
    servos: list[Servo]
    part_names: list[str]
    part_kinds: list[str]
    part_slot: list[int]
    rb_value: list[float]
    lb_value: list[float]
    rb_label: list[str]
    lb_label: list[str]
    # Power last sent to each part, or the servo position (-1 = not moved yet).
    told: list[float]
    missing: list[str]
    selected: int
    part_power: float
    part_amps: float
    part_note: str
    clock: ElapsedTime
    # Since when the Collector has been stopped, or -1 while it turns.
    collector_still_ms: float

    def runOpMode(self) -> None:
        self.cal = DriveCal()
        self.cal.load()
        self.drive = OmniDrive(self.hardwareMap, self.cal)
        self.drive.init_imu()
        self.drive.hold_enabled = False
        self.hubs = self.hardwareMap.getAll(LynxModule)
        for hub in self.hubs:
            hub.setBulkCachingMode(LynxModule.BulkCachingMode.MANUAL)
        self.parts_page = False
        self.power = self.START_POWER
        self.raw = True
        self.move = ""
        self.move_start_deg = 0.0
        self.last_move = ""
        self.last_turned = 0.0
        self.move_clock = ElapsedTime()
        self.speed_sum = [0.0, 0.0, 0.0, 0.0]
        self.speed_n = 0
        self.last_speeds = ""
        self.amps = [0.0, 0.0, 0.0, 0.0]
        self.amps_sum = [0.0, 0.0, 0.0, 0.0]
        self.amps_peak = [0.0, 0.0, 0.0, 0.0]
        self.last_amps = ""
        self.batteries = self.hardwareMap.getAll(VoltageSensor)
        self.volts = 0.0
        self.volts_low = 99.0
        self.held = 0
        self.init_parts()

        self.telemetry.addLine("Testing. Robot on the floor, room around it. Press START.")
        self.telemetry.addLine("share = DRIVE / PARTS page")
        for name in self.missing:
            self.telemetry.addLine(f"No '{name}' in the configuration: not in the PARTS list")
        self.telemetry.update()
        self.waitForStart()

        self.drive.start()
        while self.opModeIsActive():
            for hub in self.hubs:
                hub.clearBulkCache()
            g = self.gamepad1
            # Every *WasPressed() is read once per loop on both pages: an
            # unread press would wait and fire later on the other page.
            press_share = g.backWasPressed()
            press_up = g.triangleWasPressed()
            press_down = g.crossWasPressed()
            press_square = g.squareWasPressed()
            press_dpad_up = g.dpadUpWasPressed()
            press_dpad_down = g.dpadDownWasPressed()
            if press_share:
                self.parts_page = not self.parts_page
                self.drive.stop()
                self.move = ""
                self.amps = [0.0, 0.0, 0.0, 0.0]
                self.stop_parts()
            if self.parts_page:
                self.parts_loop(g, press_up, press_down, press_dpad_up, press_dpad_down)
                self.show_parts()
            else:
                self.drive_loop(g, press_up, press_down, press_square)
                self.show_drive()
        self.drive.stop()
        self.stop_parts()

    # ------------------------------------------------------------------ DRIVE page

    def drive_loop(self, g: Gamepad, press_up: bool, press_down: bool, press_square: bool) -> None:
        if press_up:
            self.power = min(1.0, self.power + self.POWER_STEP)
        if press_down:
            self.power = max(self.POWER_STEP, self.power - self.POWER_STEP)
        if press_square:
            self.raw = not self.raw
            # Switching mid-move would mix two modes into one observation.
            self.drive.stop()
            self.move = ""
        self.drive.use_corrections = not self.raw
        self.drive.update_heading()

        fwd = 0.0
        strafe = 0.0
        rot = 0.0
        move = ""
        held = 0
        if g.dpad_up:
            fwd = self.power
            move = "FORWARD"
            held = held + 1
        if g.dpad_down:
            fwd = -self.power
            move = "BACKWARD"
            held = held + 1
        if g.dpad_right:
            strafe = self.power
            move = "STRAFE RIGHT"
            held = held + 1
        if g.dpad_left:
            strafe = -self.power
            move = "STRAFE LEFT"
            held = held + 1
        if g.right_bumper:
            rot = self.power
            move = "TURN RIGHT"
            held = held + 1
        if g.left_bumper:
            rot = -self.power
            move = "TURN LEFT"
            held = held + 1
        if held != 1:
            move = ""
        self.held = held

        if move != self.move:
            if self.move != "":
                self.last_move = self.move
                self.last_turned = self.drive.heading() - self.move_start_deg
                self.last_speeds = self.wheel_speeds()
                self.last_amps = self.wheel_amps()
            self.move = move
            self.move_start_deg = self.drive.heading()
            self.move_clock.reset()
            self.speed_sum = [0.0, 0.0, 0.0, 0.0]
            self.amps_sum = [0.0, 0.0, 0.0, 0.0]
            self.amps_peak = [0.0, 0.0, 0.0, 0.0]
            self.speed_n = 0
        if move != "":
            # Current is not in the bulk read: 4 extra hub commands per
            # loop (plus the battery), acceptable in a test OpMode, and
            # only while moving.
            for i in range(4):
                self.amps[i] = self.drive.motors[i].getCurrent(CurrentUnit.AMPS)
                self.amps_peak[i] = max(self.amps_peak[i], self.amps[i])
            if len(self.batteries) > 0:
                self.volts = self.batteries[0].getVoltage()
                self.volts_low = min(self.volts_low, self.volts)
        if move != "" and self.move_clock.milliseconds() >= self.SETTLE_MS:
            for i in range(4):
                self.speed_sum[i] = self.speed_sum[i] + abs(self.drive.motors[i].getVelocity())
                self.amps_sum[i] = self.amps_sum[i] + self.amps[i]
            self.speed_n = self.speed_n + 1
        if move == "":
            self.drive.stop()
            self.amps = [0.0, 0.0, 0.0, 0.0]
        else:
            # drive()'s +rotation turns this robot left, so turning right
            # is -rot: the same flip Main applies to the right stick.
            self.drive.drive(fwd, strafe, -rot)

    def wheel_speeds(self) -> str:
        """Each wheel's average speed this move, as a % of the four's average."""
        if self.speed_n == 0:
            return "too short to measure (hold at least 1 s)"
        mean = (self.speed_sum[0] + self.speed_sum[1] + self.speed_sum[2] + self.speed_sum[3]) / 4.0
        if mean <= 0.0:
            return "no encoder counts from any wheel"
        text = ""
        slow = ""
        for i in range(4):
            pct = 100.0 * self.speed_sum[i] / mean
            text = text + f"{OmniDrive.WHEEL_NAMES[i]} {pct:.0f}%  "
            if pct < self.SLOW_PERCENT:
                slow = slow + " " + OmniDrive.WHEEL_NAMES[i]
        if slow != "":
            text = text + "| slow:" + slow
        return text

    def wheel_amps(self) -> str:
        """Each wheel's average current this move (peak in brackets)."""
        if self.speed_n == 0:
            return "too short to measure (hold at least 1 s)"
        text = ""
        for i in range(4):
            text = text + f"{OmniDrive.WHEEL_NAMES[i]} {self.amps_sum[i] / self.speed_n:.1f} ({self.amps_peak[i]:.1f})  "
        return text + "A avg (peak)"

    def show_drive(self) -> None:
        self.telemetry.addLine("DRIVE page (share: PARTS)")
        mode = "RAW (mix + motor directions only)" if self.raw else "CALIBRATED (as Main drives)"
        self.telemetry.addData("Mode", mode + ", square to switch")
        self.telemetry.addData("Power", f"{self.power:.1f} (triangle +, cross -)")
        if self.move != "":
            turned = self.drive.heading() - self.move_start_deg
            self.telemetry.addData("Driving", f"{self.move}, turned {turned:+.1f} deg so far")
            self.telemetry.addData("Wheel speeds", self.wheel_speeds())
            self.telemetry.addData("Wheel current", self.wheel_amps())
        elif self.held > 1:
            self.telemetry.addData("Driving", "stopped: one button at a time")
        else:
            self.telemetry.addData("Driving", "stopped: hold a dpad direction or a bumper")
        if self.last_move != "":
            self.telemetry.addData("Last move", f"{self.last_move}, turned {self.last_turned:+.1f} deg")
            self.telemetry.addData("Last wheel speeds", self.last_speeds)
            self.telemetry.addData("Last wheel current", self.last_amps)
        if not self.raw and not self.cal.loaded:
            self.telemetry.addLine("No calibration file: CALIBRATED drives the same as RAW")
        for i in range(4):
            m = self.drive.motors[i]
            self.telemetry.addData(OmniDrive.WHEEL_NAMES[i], f"told {m.getPower():+.2f}, encoder {m.getVelocity():+.0f} ticks/s, {self.amps[i]:.2f} A")
        if self.volts > 0:
            self.telemetry.addData("Battery", f"{self.volts:.2f} V (lowest while moving {self.volts_low:.2f} V)")
        self.telemetry.update()

    # ------------------------------------------------------------------ PARTS page

    def init_parts(self) -> None:
        self.motors = []
        self.crservos = []
        self.servos = []
        self.part_names = []
        self.part_kinds = []
        self.part_slot = []
        self.rb_value = []
        self.lb_value = []
        self.rb_label = []
        self.lb_label = []
        self.told = []
        self.missing = []
        self.selected = 0
        self.part_power = self.PART_START_POWER
        self.part_amps = 0.0
        self.part_note = ""
        self.clock = ElapsedTime()
        self.collector_still_ms = -1.0

        # Set up exactly as Main does: a run mode survives from the last
        # OpMode, and RUN_USING_ENCODER would turn power into a speed target.
        self.collector = self.hardwareMap.get(DcMotorEx, "Collector")
        self.collector.setDirection(DcMotorSimple.Direction.REVERSE)
        shooter = self.hardwareMap.get(DcMotorEx, "shooter")
        shooter.setMode(DcMotor.RunMode.RUN_WITHOUT_ENCODER)
        climber = self.hardwareMap.get(DcMotorEx, "Climber")
        climber.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
        climber.setMode(DcMotor.RunMode.RUN_WITHOUT_ENCODER)
        fishing = self.hardwareMap.get(DcMotorEx, "Fishing")
        fishing.setDirection(DcMotorSimple.Direction.REVERSE)
        fishing.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
        climb_upper = self.hardwareMap.get(CRServo, "ClimbUpper")
        climb_upper.setDirection(DcMotorSimple.Direction.FORWARD)
        fixator = self.hardwareMap.get(CRServo, "FixatorRelease")

        self.add_motor("Collector", self.collector, 1.0, "pickup", "reverse")
        self.add_motor("shooter", shooter, 1.0, "shoot", "backwards")
        self.add_motor("Climber", climber, self.CLIMBER_UP, "up", "down")
        self.add_motor("Chain (Fishing)", fishing, -1.0, "up", "down")
        self.add_crservo("ClimbUpper", climb_upper, self.CLIMB_POWER, "up", "down")
        second = self.hardwareMap.tryGet(CRServo, self.SECOND_CLIMB_NAME)
        if second is None:
            self.missing.append(self.SECOND_CLIMB_NAME)
        else:
            second.setDirection(DcMotorSimple.Direction.FORWARD)
            self.add_crservo(self.SECOND_CLIMB_NAME, second, self.SECOND_CLIMB_POWER, "up", "down")
        self.add_crservo("FixatorRelease", fixator, self.FIXATOR_POWER, "release", "wind back")
        self.add_servo("ChainStop", self.hardwareMap.get(Servo, "ChainStop"), self.CHAIN_STOP_START, "open (start)", self.CHAIN_STOP_ENGAGED, "closed (brake)")
        self.add_servo("chainDrop", self.hardwareMap.get(Servo, "chainDrop"), self.CHAIN_DROP_FISHING, "dropped", self.CHAIN_DROP_START, "start")
        clutch = self.hardwareMap.tryGet(Servo, self.CLUTCH_NAME)
        if clutch is None:
            self.missing.append(self.CLUTCH_NAME)
        else:
            self.add_servo(self.CLUTCH_NAME, clutch, self.CLUTCH_DEPLOYED, "deployed", self.CLUTCH_RETRACTED, "retracted")

    def add_part(self, name: str, kind: str, slot: int, rb: float, rb_label: str, lb: float, lb_label: str, told: float) -> None:
        self.part_names.append(name)
        self.part_kinds.append(kind)
        self.part_slot.append(slot)
        self.rb_value.append(rb)
        self.lb_value.append(lb)
        self.rb_label.append(rb_label)
        self.lb_label.append(lb_label)
        self.told.append(told)

    def add_motor(self, name: str, motor: DcMotorEx, rb_sign: float, rb_label: str, lb_label: str) -> None:
        self.motors.append(motor)
        self.add_part(name, "motor", len(self.motors) - 1, rb_sign, rb_label, -rb_sign, lb_label, 0.0)

    def add_crservo(self, name: str, servo: CRServo, rb_sign: float, rb_label: str, lb_label: str) -> None:
        self.crservos.append(servo)
        self.add_part(name, "crservo", len(self.crservos) - 1, rb_sign, rb_label, -rb_sign, lb_label, 0.0)

    def add_servo(self, name: str, servo: Servo, rb_pos: float, rb_label: str, lb_pos: float, lb_label: str) -> None:
        self.servos.append(servo)
        self.add_part(name, "servo", len(self.servos) - 1, rb_pos, rb_label, lb_pos, lb_label, -1.0)

    def set_power(self, i: int, power: float) -> None:
        # The SDK only sends a power that changed, so this is cheap every loop.
        if self.part_kinds[i] == "motor":
            self.motors[self.part_slot[i]].setPower(power)
        else:
            self.crservos[self.part_slot[i]].setPower(power)
        self.told[i] = power

    def set_position(self, i: int, position: float) -> None:
        position = min(1.0, max(0.0, position))
        # Main's rule: the clutch goes in only onto a Collector that has been
        # stopped for CLUTCH_STILL_MS; pulling it back is allowed any time.
        if self.part_names[i] == self.CLUTCH_NAME and position != self.CLUTCH_RETRACTED and not self.collector_still():
            self.part_note = "refused: the Collector is still turning (Main never deploys onto it)"
            return
        self.servos[self.part_slot[i]].setPosition(position)
        self.told[i] = position
        self.part_note = ""

    def collector_still(self) -> bool:
        return self.collector_still_ms >= 0 and self.clock.milliseconds() - self.collector_still_ms >= self.CLUTCH_STILL_MS

    def track_collector(self) -> None:
        # From the bulk read made for this loop anyway: no extra hub command.
        if abs(self.collector.getVelocity()) >= self.CLUTCH_STOPPED_TPS:
            self.collector_still_ms = -1.0
        elif self.collector_still_ms < 0:
            self.collector_still_ms = self.clock.milliseconds()

    def stop_parts(self) -> None:
        for i in range(len(self.part_names)):
            if self.part_kinds[i] != "servo":
                self.set_power(i, 0.0)
        self.part_amps = 0.0

    def parts_loop(self, g: Gamepad, press_up: bool, press_down: bool, press_dpad_up: bool, press_dpad_down: bool) -> None:
        self.track_collector()
        count = len(self.part_names)
        if press_dpad_up or press_dpad_down:
            self.stop_parts()
            self.part_note = ""
            step = 1
            if press_dpad_up:
                step = count - 1
            self.selected = (self.selected + step) % count
        i = self.selected
        if self.part_kinds[i] == "servo":
            if g.right_bumper:
                self.set_position(i, self.rb_value[i])
            elif g.left_bumper:
                self.set_position(i, self.lb_value[i])
            elif press_up or press_down:
                if self.told[i] < 0:
                    self.part_note = "press a bumper first: its position is not known yet"
                elif press_up:
                    self.set_position(i, self.told[i] + self.SERVO_STEP)
                else:
                    self.set_position(i, self.told[i] - self.SERVO_STEP)
            return
        if press_up:
            self.part_power = min(1.0, self.part_power + self.POWER_STEP)
        if press_down:
            self.part_power = max(self.POWER_STEP, self.part_power - self.POWER_STEP)
        power = 0.0
        if g.right_bumper and not g.left_bumper:
            power = self.rb_value[i] * self.part_power
        elif g.left_bumper and not g.right_bumper:
            power = self.lb_value[i] * self.part_power
        self.set_power(i, power)
        # Current is its own hub command (not in the bulk read): only for
        # the selected motor, and only while it runs.
        if self.part_kinds[i] == "motor" and power != 0.0:
            self.part_amps = self.motors[self.part_slot[i]].getCurrent(CurrentUnit.AMPS)
        else:
            self.part_amps = 0.0

    def part_state(self, i: int) -> str:
        if self.part_kinds[i] == "servo":
            if self.told[i] < 0:
                return "not moved yet"
            name = "custom"
            if abs(self.told[i] - self.rb_value[i]) < 0.001:
                name = self.rb_label[i]
            elif abs(self.told[i] - self.lb_value[i]) < 0.001:
                name = self.lb_label[i]
            return f"{self.told[i]:.2f} ({name})"
        if self.told[i] == 0.0:
            return "stopped"
        way = self.rb_label[i]
        if self.told[i] * self.rb_value[i] < 0:
            way = self.lb_label[i]
        return f"{way} {abs(self.told[i]):.1f}"

    def show_parts(self) -> None:
        self.telemetry.addLine("PARTS page (share: DRIVE), dpad up/down = choose")
        for i in range(len(self.part_names)):
            mark = "   "
            if i == self.selected:
                mark = ">> "
            self.telemetry.addLine(f"{mark}{self.part_names[i]}: {self.part_state(i)}")
        i = self.selected
        self.telemetry.addLine("")
        if self.part_kinds[i] == "servo":
            self.telemetry.addLine(f"RB = {self.rb_label[i]} ({self.rb_value[i]:.2f}), LB = {self.lb_label[i]} ({self.lb_value[i]:.2f})")
            self.telemetry.addLine(f"triangle / cross = {self.SERVO_STEP:+.2f} / {-self.SERVO_STEP:+.2f}")
        else:
            self.telemetry.addLine(f"hold RB = {self.rb_label[i]}, hold LB = {self.lb_label[i]}")
            self.telemetry.addData("Power", f"{self.part_power:.1f} (triangle +, cross -)")
        if self.part_kinds[i] == "motor":
            m = self.motors[self.part_slot[i]]
            self.telemetry.addData("Encoder", f"{m.getVelocity():+.0f} ticks/s")
            self.telemetry.addData("Current", f"{self.part_amps:.2f} A")
        self.telemetry.addData("Collector speed", f"{self.collector.getVelocity():+.0f} ticks/s (clutch deploys only under {self.CLUTCH_STOPPED_TPS:.0f} for {self.CLUTCH_STILL_MS:.0f} ms)")
        if self.part_note != "":
            self.telemetry.addLine("!! " + self.part_note)
        self.telemetry.update()
