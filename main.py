"""Starter pack for Gicko, generated 2026-09-20 from hardware configuration "FGC2026-Incheon".

Press INIT on the Driver Hub: everything above waitForStart() runs once.
Press START: the while loop runs until STOP.
"""

# ── pyftc:config name="FGC2026-Incheon" fingerprint="c841abeba9d5c0ab" generated="2026-09-20" ──

# ── pyftc:imports ──
from typing import Any


from ftc.hardware import CRServo, DcMotor, DcMotorControllerEx, DcMotorSimple, Servo
from ftc.navigation import AngleUnit
from ftc.opmode import LinearOpMode, TeleOp
from ftc.util import ElapsedTime
# ── pyftc:imports:end ──

#Cycle Phase type helper
class Cycle:
    """One button-driven phase counter: press cycles phase 0..count and wraps."""
    count: int
    phase: int
    last_ms: float

    def __init__(self, count: int, last_ms: float) -> None:
        self.count = count
        self.phase = 0
        self.last_ms = last_ms


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
    fixator_release: Servo
    # ── pyftc:devices:end ──
    
    #CyclePhase Vars
    cycle_register: dict[str, Cycle] = {}
    cycle_List: list[str] = []
    timer: ElapsedTime = ElapsedTime()
    DEBOUNCE_MS: float = 500.0   # minimum time between two phase changes
    
    #CyclePhase Main
    def register_cyclePhase(self, name: str, count: int) -> None:
        self.cycle_register[name] = Cycle(count-1, self.timer.milliseconds())
        self.cycle_List.append(name)

    def cyclePhase(self, name: str, pressed: bool) -> None:
        """Advance one cycle. `pressed` must be read fresh every loop: a button
        passed at registration time would be a copy of its value back then."""
        cycle = self.cycle_register[name]
        if pressed and self.timer.milliseconds() - cycle.last_ms > self.DEBOUNCE_MS:
            if cycle.phase >= cycle.count:
                cycle.phase = 0
            else:
                cycle.phase = cycle.phase + 1
            cycle.last_ms = self.timer.milliseconds()

    def phase_of(self, name: str) -> int:
        return self.cycle_register[name].phase
    def floattobool(self, input: float)  -> bool:
        if input<=0.5:
            return False
        else:
            return True
    #Defining collector/shooterintake
    def BallCollector(self) -> DcMotor:
        self.tobesplit.setDirection(DcMotorSimple.Direction.FORWARD)
        return self.tobesplit
    def shooter_intake(self) -> DcMotor:
        self.tobesplit.setDirection(DcMotorSimple.Direction.REVERSE)
        return self.tobesplit
    #Op Modes
    def runOpMode(self) -> None:
        # ── On ready: runs once when INIT is pressed ──
        self.tobesplit = self.hardwareMap.get(DcMotor, "Collector")#Split between to modes collector and intake
        # ── pyftc:init ──
        self.shooter = self.hardwareMap.get(DcMotor, "shooter")
        self.climber = self.hardwareMap.get(DcMotor, "Climber")
        self.fishing = self.hardwareMap.get(DcMotor, "Fishing")
        self.lb = self.hardwareMap.get(DcMotor, "LB")
        self.rb = self.hardwareMap.get(DcMotor, "RB")
        self.lf = self.hardwareMap.get(DcMotor, "LF")
        self.rf = self.hardwareMap.get(DcMotor, "RF")
        self.chain_drop = self.hardwareMap.get(Servo, "chainDrop")
        self.chain_stop = self.hardwareMap.get(Servo, "ChainStop")
        self.fixator_release = self.hardwareMap.get(Servo, "FixatorRelease")

        # ── pyftc:init:end ──
        self.telemetry.addLine("Ready. Press START.")
        self.telemetry.update()
        self.waitForStart()

        # RegisterPhases
        self.register_cyclePhase(name="MagDump", count=3)
        self.register_cyclePhase(name="BallPickup", count=2)
        self.register_cyclePhase(name="DriveDirection", count=2)
        self.register_cyclePhase(name="ClimbDirection", count=2)
        self.timer.reset()

        #Fishing
        self.fishing.setDirection(DcMotorSimple.Direction.REVERSE)
        self.fishing.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
        self.chain_drop.setPosition(0)

        #ChainStop
        self.chain_stop.setPosition(0.7)
        self.EnteredFishing: bool = False
        # ── On start: loops until STOP is pressed ──
        self.InUse="Free" #Muttually exclusive split
        while self.opModeIsActive():

            #DriveDirection
            DriveDirection=self.phase_of("DriveDirection")
            if DriveDirection==0:
                self.rf.setDirection(DcMotorSimple.Direction.REVERSE)
                self.lb.setDirection(DcMotorSimple.Direction.REVERSE)
                self.lf.setDirection(DcMotorSimple.Direction.FORWARD)
                self.rb.setDirection(DcMotorSimple.Direction.FORWARD)
                self.telemetry.addData("DDirection", 0)
            else:
                self.rf.setDirection(DcMotorSimple.Direction.FORWARD)
                self.lb.setDirection(DcMotorSimple.Direction.FORWARD)
                self.lf.setDirection(DcMotorSimple.Direction.REVERSE)
                self.rb.setDirection(DcMotorSimple.Direction.REVERSE)
                self.telemetry.addData("DDirection", 1)

            #OmniWheelMovement
            self.lf.setPower(self.gamepad1.right_stick_y-self.gamepad1.right_stick_x)
            self.rf.setPower(self.gamepad1.right_stick_y+self.gamepad1.right_stick_x)
            self.lb.setPower(-self.gamepad1.right_stick_y-self.gamepad1.right_stick_x)
            self.rb.setPower(-self.gamepad1.right_stick_y+self.gamepad1.right_stick_x)

            self.lf.setPower(-self.gamepad1.left_stick_x)
            self.rf.setPower(self.gamepad1.left_stick_x)
            self.lb.setPower(self.gamepad1.left_stick_x)
            self.rb.setPower(-self.gamepad1.left_stick_x)
            #Shooter and shooter intake
            MagDump: int = self.phase_of("MagDump")
            if MagDump==1 and self.InUse=="Free":  
                self.shooter.setPower(0.8)
                self.telemetry.addData("MagDump", "Shooter spinning up")
                self.InUse="MagDump"
            elif MagDump==2 and self.InUse=="MagDump": 
                self.shooter_intake().setPower(1)
                self.telemetry.addData("MagDump", "Shooter shooting")
            elif MagDump==0 and self.InUse=="MagDump":
                self.shooter_intake().setPower(0)
                self.shooter.setPower(0)
                self.telemetry.addData("MagDump", "Shooter off")
                self.InUse="Free"
            
            #BallPickup
            BallPickup=self.phase_of(name="BallPickup")
            if BallPickup==1 and self.InUse=="Free":
                self.BallCollector().setPower(1)
                self.InUse="BallPickup"
            elif BallPickup==0 and self.InUse=="BallPickup":
                self.BallCollector().setPower(0)
                self.InUse="Free"

            #Fishing
            if self.gamepad1.dpad_down:
                self.chain_drop.setPosition(0.25)
                self.EnteredFishing = True
                self.fishing.setPower(1)
            elif self.gamepad1.dpad_up:
                self.fishing.setPower(-1)
            else:
                self.fishing.setPower(0)
            
            #ChainStop
            if self.gamepad1.leftBumperWasPressed() and self.EnteredFishing:
                self.chain_stop.setPosition(0.4)
            
            #cyclePhase
            self.cyclePhase("MagDump", self.gamepad1.cross)
            self.cyclePhase("BallPickup", self.gamepad1.circle)
            self.cyclePhase(name="DriveDirection", pressed=self.gamepad1.right_bumper)
            self.cyclePhase(name="ClimbDirection", pressed=self.floattobool(self.gamepad1.right_trigger))
            #telemetry
            self.telemetry.update()
            