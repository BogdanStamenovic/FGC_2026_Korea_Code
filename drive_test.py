"""Drive Test: drives in one pure direction at a time, so you can see whether
"forward" really goes forward, "strafe right" really goes right, and so on.
Put the robot on the floor with room around it.

The robot only moves while a button is held; let go and it stops. On gamepad 1:
  dpad up / down        forward / backward
  dpad right / left     strafe right / left
  right / left bumper   turn right / left (on the spot)
  triangle / cross      power +0.1 / -0.1 (starts at 0.4)
  square                RAW <-> CALIBRATED

RAW (the default) is the plain wheel mix and motor directions from drive.py,
nothing else: if RAW goes the wrong way, the mix or a motor direction is
wrong. CALIBRATED adds the Calibration OpMode's corrections, exactly as Main
drives (without heading hold): if RAW is right but CALIBRATED is not, the
calibration file is. Holding two direction buttons at once does nothing.

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

from ftc.hardware import LynxModule, VoltageSensor
from ftc.navigation import CurrentUnit
from ftc.opmode import LinearOpMode, TeleOp
from ftc.util import ElapsedTime
from drive import OmniDrive
from drive_cal import DriveCal


@TeleOp(name="Drive Test", group="pyftc")
class DriveTest(LinearOpMode):
    POWER_STEP: float = 0.1
    # Wheel speeds are averaged from this long after a move starts: while the
    # robot accelerates, the wheels are not yet at their own speed.
    SETTLE_MS: float = 300.0
    # A wheel below this share of the average is called out as slow.
    SLOW_PERCENT: float = 92.0
    START_POWER: float = 0.4

    cal: DriveCal
    drive: OmniDrive
    hubs: list[LynxModule]
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

    def runOpMode(self) -> None:
        self.cal = DriveCal()
        self.cal.load()
        self.drive = OmniDrive(self.hardwareMap, self.cal)
        self.drive.init_imu()
        self.drive.hold_enabled = False
        self.hubs = self.hardwareMap.getAll(LynxModule)
        for hub in self.hubs:
            hub.setBulkCachingMode(LynxModule.BulkCachingMode.MANUAL)
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

        self.telemetry.addLine("Drive Test. Robot on the floor, room around it. Press START.")
        self.telemetry.addLine("Hold dpad = forward/back/strafe, bumpers = turn, square = RAW/CALIBRATED")
        self.telemetry.update()
        self.waitForStart()

        self.drive.start()
        while self.opModeIsActive():
            for hub in self.hubs:
                hub.clearBulkCache()
            g = self.gamepad1
            if g.triangleWasPressed():
                self.power = min(1.0, self.power + self.POWER_STEP)
            if g.crossWasPressed():
                self.power = max(self.POWER_STEP, self.power - self.POWER_STEP)
            if g.squareWasPressed():
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
            self.show(held)
        self.drive.stop()

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

    def show(self, held: int) -> None:
        mode = "RAW (mix + motor directions only)" if self.raw else "CALIBRATED (as Main drives)"
        self.telemetry.addData("Mode", mode + ", square to switch")
        self.telemetry.addData("Power", f"{self.power:.1f} (triangle +, cross -)")
        if self.move != "":
            turned = self.drive.heading() - self.move_start_deg
            self.telemetry.addData("Driving", f"{self.move}, turned {turned:+.1f} deg so far")
            self.telemetry.addData("Wheel speeds", self.wheel_speeds())
            self.telemetry.addData("Wheel current", self.wheel_amps())
        elif held > 1:
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
