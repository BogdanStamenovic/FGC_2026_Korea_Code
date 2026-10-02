"""Aftercare: run after a match to put the climbing parts back by hand.

Nothing moves at INIT or START; every part moves only while its button is
held (motors, fixator) or when its button is pressed (servos).

Gamepad 1:
  dpad up / down        chain motor ("Fishing") up / down, while held
  dpad right / left     fixator release: release / wind back, while held
  right bumper          chain stop OPEN  (brake released, the start position)
  right trigger         chain stop CLOSE (brake engaged)
  left bumper           chain drop OPEN  (chain dropped)
  left trigger          chain drop CLOSE (the start position)

Gamepad 2 (wheel check, unchanged): dpad left/up/right/down spins LF/RF/RB/LB.

The servo positions, directions and powers are copies of main.py's: change
them there and here together, or Aftercare resets a part to where main.py no
longer starts it.

Its hardware lookups match the "FGC2026-Incheon" configuration; asking for a
device that isn't configured (the old "ShooterIntake") or with the wrong type
(FixatorRelease as a Servo) crashes the OpMode at INIT.
"""

# ── pyftc:config name="FGC2026-Incheon" fingerprint="c841abeba9d5c0ab" generated="2026-09-20" ──

# ── pyftc:imports ──
from ftc.hardware import CRServo, DcMotor, DcMotorEx, DcMotorSimple, Servo
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

    # main.py: CHAIN_STOP_START / CHAIN_STOP_ENGAGED, CHAIN_DROP_START / CHAIN_DROP_FISHING.
    CHAIN_STOP_OPEN: float = 0.7
    CHAIN_STOP_CLOSED: float = 0.4
    CHAIN_DROP_OPEN: float = 0.25
    CHAIN_DROP_CLOSED: float = 0.0
    # main.py: the fixator releases at +FIXATOR_POWER, the chain goes up at
    # -1 with the Fishing motor REVERSEd.
    FIXATOR_POWER: float = 1.0
    CHAIN_POWER: float = 1.0
    TRIGGER_PRESSED: float = 0.5

    chain_stop_state: str
    chain_drop_state: str

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
        self.fishing.setDirection(DcMotorSimple.Direction.REVERSE)
        self.fishing.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
        self.fishing.setMode(DcMotor.RunMode.RUN_WITHOUT_ENCODER)
        self.fixator_release.setDirection(DcMotorSimple.Direction.FORWARD)
        # A servo holds no position until it is first told one, so until a
        # button is pressed its state is unknown.
        self.chain_stop_state = "not moved yet"
        self.chain_drop_state = "not moved yet"
        self.telemetry.addLine("Ready. Press START.")
        self.telemetry.update()
        self.waitForStart()
        # ── On start: loops until STOP is pressed ──
        while self.opModeIsActive():
            g = self.gamepad1

            chain = 0.0
            if g.dpad_up:
                chain = -self.CHAIN_POWER
            elif g.dpad_down:
                chain = self.CHAIN_POWER
            self.fishing.setPower(chain)

            fixator = 0.0
            if g.dpad_right:
                fixator = self.FIXATOR_POWER
            elif g.dpad_left:
                fixator = -self.FIXATOR_POWER
            self.fixator_release.setPower(fixator)

            if g.right_bumper:
                self.chain_stop.setPosition(self.CHAIN_STOP_OPEN)
                self.chain_stop_state = "OPEN"
            elif g.right_trigger > self.TRIGGER_PRESSED:
                self.chain_stop.setPosition(self.CHAIN_STOP_CLOSED)
                self.chain_stop_state = "CLOSED"
            if g.left_bumper:
                self.chain_drop.setPosition(self.CHAIN_DROP_OPEN)
                self.chain_drop_state = "OPEN"
            elif g.left_trigger > self.TRIGGER_PRESSED:
                self.chain_drop.setPosition(self.CHAIN_DROP_CLOSED)
                self.chain_drop_state = "CLOSED"

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

            self.telemetry.addLine(f"Chain motor: {self.direction_name(chain, 'down', 'up')}   (dpad up/down)")
            self.telemetry.addLine(f"Fixator: {self.direction_name(fixator, 'releasing', 'winding back')}   (dpad right/left)")
            self.telemetry.addLine(f"Chain stop: {self.chain_stop_state}   (RB open / RT close)")
            self.telemetry.addLine(f"Chain drop: {self.chain_drop_state}   (LB open / LT close)")
            self.telemetry.update()

    def direction_name(self, power: float, positive: str, negative: str) -> str:
        if power > 0:
            return positive
        if power < 0:
            return negative
        return "stopped"
