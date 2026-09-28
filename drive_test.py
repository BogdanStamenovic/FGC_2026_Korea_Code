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
0 degrees).
"""

from ftc.hardware import LynxModule
from ftc.opmode import LinearOpMode, TeleOp
from drive import OmniDrive
from drive_cal import DriveCal


@TeleOp(name="Drive Test", group="pyftc")
class DriveTest(LinearOpMode):
    POWER_STEP: float = 0.1
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
                self.move = move
                self.move_start_deg = self.drive.heading()
            if move == "":
                self.drive.stop()
            else:
                # drive()'s +rotation turns this robot left, so turning right
                # is -rot: the same flip Main applies to the right stick.
                self.drive.drive(fwd, strafe, -rot)
            self.show(held)
        self.drive.stop()

    def show(self, held: int) -> None:
        mode = "RAW (mix + motor directions only)" if self.raw else "CALIBRATED (as Main drives)"
        self.telemetry.addData("Mode", mode + ", square to switch")
        self.telemetry.addData("Power", f"{self.power:.1f} (triangle +, cross -)")
        if self.move != "":
            turned = self.drive.heading() - self.move_start_deg
            self.telemetry.addData("Driving", f"{self.move}, turned {turned:+.1f} deg so far")
        elif held > 1:
            self.telemetry.addData("Driving", "stopped: one button at a time")
        else:
            self.telemetry.addData("Driving", "stopped: hold a dpad direction or a bumper")
        if self.last_move != "":
            self.telemetry.addData("Last move", f"{self.last_move}, turned {self.last_turned:+.1f} deg")
        if not self.raw and not self.cal.loaded:
            self.telemetry.addLine("No calibration file: CALIBRATED drives the same as RAW")
        for i in range(4):
            m = self.drive.motors[i]
            self.telemetry.addData(OmniDrive.WHEEL_NAMES[i], f"told {m.getPower():+.2f}, encoder {m.getVelocity():+.0f} ticks/s")
        self.telemetry.update()
