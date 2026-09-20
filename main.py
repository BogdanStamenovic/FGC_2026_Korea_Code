"""Starter pack for Gicko, generated 2026-09-20 from hardware configuration "FGC2026-Incheon".

Press INIT on the Driver Hub: everything above waitForStart() runs once.
Press START: the while loop runs until STOP.
"""

# ── pyftc:config name="FGC2026-Incheon" fingerprint="c841abeba9d5c0ab" generated="2026-09-20" ──

# ── pyftc:imports ──
from ftc.hardware import CRServo, DcMotor, DcMotorSimple, Servo
from ftc.navigation import AngleUnit
from ftc.opmode import LinearOpMode, TeleOp
# ── pyftc:imports:end ──

@TeleOp(name="Main", group="pyftc")
class Main(LinearOpMode):
    # ── pyftc:devices ──
    collector: DcMotor
    shooter: DcMotor
    climber: DcMotor
    fishing: DcMotor
    lb: DcMotor
    rb: DcMotor
    lf: DcMotor
    rf: DcMotor
    chain_drop: Servo
    chain_stop: Servo
    shooter_intake: CRServo
    fixator_release: Servo
    # ── pyftc:devices:end ──

    def runOpMode(self) -> None:
        # ── On ready: runs once when INIT is pressed ──
        # ── pyftc:init ──
        self.collector = self.hardwareMap.get(DcMotor, "Collector")
        self.shooter = self.hardwareMap.get(DcMotor, "shooter")
        self.climber = self.hardwareMap.get(DcMotor, "Climber")
        self.fishing = self.hardwareMap.get(DcMotor, "Fishing")
        self.lb = self.hardwareMap.get(DcMotor, "LB")
        self.rb = self.hardwareMap.get(DcMotor, "RB")
        self.lf = self.hardwareMap.get(DcMotor, "LF")
        self.rf = self.hardwareMap.get(DcMotor, "RF")
        self.chain_drop = self.hardwareMap.get(Servo, "chainDrop")
        self.chain_stop = self.hardwareMap.get(Servo, "ChainStop")
        self.shooter_intake = self.hardwareMap.get(CRServo, "ShooterIntake")
        self.fixator_release = self.hardwareMap.get(Servo, "FixatorRelease")
        chain_drop_position = 0.5  # servo jumps here on START; set your starting position
        chain_stop_position = 0.5  # servo jumps here on START; set your starting position
        fixator_release_position = 0.5  # servo jumps here on START; set your starting position
        # ── pyftc:init:end ──

        self.telemetry.addLine("Ready. Press START.")
        self.telemetry.update()
        self.waitForStart()
        self.rf.setDirection(DcMotorSimple.Direction.REVERSE)
        self.lb.setDirection(DcMotorSimple.Direction.REVERSE)
        # ── On start: loops until STOP is pressed ──
        while self.opModeIsActive():
            #OmniWheelMovement
            self.lf.setPower(-self.gamepad1.right_stick_y-self.gamepad1.right_stick_x)
            self.rf.setPower(-self.gamepad1.right_stick_y+self.gamepad1.right_stick_x)
            self.lb.setPower(self.gamepad1.right_stick_y-self.gamepad1.right_stick_x)
            self.rb.setPower(self.gamepad1.right_stick_y+self.gamepad1.right_stick_x)
            
            
            #telemetry
            self.telemetry.update()
            