"""Aftercare: an empty OpMode to run after a match (resetting mechanisms,
saving data for the next match). Nothing in it yet.

Its hardware lookups match the "FGC2026-Incheon" configuration; asking for a
device that isn't configured (the old "ShooterIntake") or with the wrong type
(FixatorRelease as a Servo) crashes the OpMode at INIT.
"""

# ── pyftc:config name="FGC2026-Incheon" fingerprint="c841abeba9d5c0ab" generated="2026-09-20" ──

# ── pyftc:imports ──
from ftc.hardware import CRServo, DcMotor, DcMotorEx, Servo
from ftc.opmode import LinearOpMode, TeleOp
# ── pyftc:imports:end ──


@TeleOp(name="aftercare", group="pyftc")
class aftercare(LinearOpMode):
    # ── pyftc:devices ──
    collector: DcMotorEx
    shooter: DcMotorEx
    climber: DcMotor
    fishing: DcMotor
    lb: DcMotor
    rb: DcMotor
    lf: DcMotor
    rf: DcMotor
    chain_drop: Servo
    chain_stop: Servo
    fixator_release: CRServo
    climb_upper: CRServo
    # ── pyftc:devices:end ──

    def runOpMode(self) -> None:
        # ── On ready: runs once when INIT is pressed ──
        # ── pyftc:init ──
        self.collector = self.hardwareMap.get(DcMotorEx, "Collector")
        self.shooter = self.hardwareMap.get(DcMotorEx, "shooter")
        self.climber = self.hardwareMap.get(DcMotor, "Climber")
        self.fishing = self.hardwareMap.get(DcMotor, "Fishing")
        self.lb = self.hardwareMap.get(DcMotor, "LB")
        self.rb = self.hardwareMap.get(DcMotor, "RB")
        self.lf = self.hardwareMap.get(DcMotor, "LF")
        self.rf = self.hardwareMap.get(DcMotor, "RF")
        self.chain_drop = self.hardwareMap.get(Servo, "chainDrop")
        self.chain_stop = self.hardwareMap.get(Servo, "ChainStop")
        self.fixator_release = self.hardwareMap.get(CRServo, "FixatorRelease")
        self.climb_upper = self.hardwareMap.get(CRServo, "ClimbUpper")
        # ── pyftc:init:end ──
        self.telemetry.addLine("Ready. Press START.")
        self.telemetry.update()
        self.waitForStart()
        # ── On start: loops until STOP is pressed ──
        while self.opModeIsActive():
            if self.gamepad2.dpad_left:
                self.lf.setPower(1)
            else:
                self.lf.setPower(0)
            if self.gamepad2.dpad_up:
                self.rf.setPower(1)
            else:
                self.rf.setPower(0)
            if self.gamepad2.dpad_right:
                self.rb.setPower(1)
            else:
                self.rb.setPower(0)
            if self.gamepad2.dpad_down:
                self.lb.setPower(1)
            else:
                self.lb.setPower(0)
            self.telemetry.update()
