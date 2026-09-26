"""Starter pack for Gicko, generated 2026-09-20 from hardware configuration "FGC2026-Incheon".

Press INIT on the Driver Hub: everything above waitForStart() runs once.
Press START: the while loop runs until STOP.
"""

# ── pyftc:config name="FGC2026-Incheon" fingerprint="c841abeba9d5c0ab" generated="2026-09-20" ──

# ── pyftc:imports ──
from ftc.hardware import CRServo, DcMotor, DcMotorControllerEx, DcMotorEx, DcMotorSimple, Servo
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
    ClimbUpper: CRServo
    # ── pyftc:devices:end ──
    #CyclePhase Vars
    cycle_register: dict[str, Cycle] = {}
    cycle_List: list[str] = []
    timer: ElapsedTime = ElapsedTime()
    DEBOUNCE_MS: float = 250.0   # minimum time between two phase changes
    
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
    def BallCollector(self) -> DcMotorEx:
        self.tobesplit.setDirection(DcMotorSimple.Direction.FORWARD)
        return self.tobesplit
    def shooter_intake(self) -> DcMotorEx:
        self.tobesplit.setDirection(DcMotorSimple.Direction.REVERSE)
        return self.tobesplit
    #Op Modes
    def runOpMode(self) -> None:
        # ── On ready: runs once when INIT is pressed ──
        self.tobesplit = self.hardwareMap.get(DcMotorEx, "Collector")#Split between to modes collector and intake
        # ── pyftc:init ──
        self.ClimbUpper = self.hardwareMap.get(CRServo, "ClimbUpper")
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

        # ── pyftc:init:end ──
        self.telemetry.addLine("Ready. Press START.")
        self.telemetry.update()
        self.waitForStart()

        # -- Driver init --
        self.rf.setDirection(DcMotorSimple.Direction.REVERSE)
        self.lb.setDirection(DcMotorSimple.Direction.REVERSE)
        self.lf.setDirection(DcMotorSimple.Direction.FORWARD)
        self.rb.setDirection(DcMotorSimple.Direction.FORWARD)

        # RegisterPhases
        self.register_cyclePhase(name="MagDump", count=3)
        self.register_cyclePhase(name="BallPickup", count=2)
        self.register_cyclePhase(name="ClimbDirection", count=2)
        self.register_cyclePhase(name="ClimbScaffold", count=2)
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
        self.started=False
        self.prime_velocity=0.0
        self.last_start=False
        # -- DidUseFixator?
        self.DidUseFixator=False
        while self.opModeIsActive():

            #OmniWheelMovement
            self.lf.setPower(self.gamepad1.right_stick_y-self.gamepad1.right_stick_x+self.gamepad1.left_stick_x)
            self.rf.setPower(self.gamepad1.right_stick_y+self.gamepad1.right_stick_x-self.gamepad1.left_stick_x)
            self.lb.setPower(-self.gamepad1.right_stick_y-self.gamepad1.right_stick_x-self.gamepad1.left_stick_x)
            self.rb.setPower(-self.gamepad1.right_stick_y+self.gamepad1.right_stick_x+self.gamepad1.left_stick_x)
            velocity = self.shooter.getVelocity()
            self.telemetry.addData("Prime Velocity", velocity)
            #Shooter and shooter intake

            MagDump: int = self.phase_of("MagDump")
            if MagDump==1 and self.InUse=="Free":  
                self.shooter_intake().setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
                self.shooter.setPower(1)
                self.telemetry.addData("MagDump", "Shooter spinning up")
                self.InUse="MagDump"
            elif MagDump==2 and self.InUse=="MagDump": 
                self.started = True
                self.telemetry.addData("MagDump", "Shooter shooting")
            elif MagDump==0 and self.InUse=="MagDump":
                self.shooter_intake().setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.FLOAT)
                self.shooter_intake().setPower(0)
                self.shooter.setPower(0)
                self.started=False
                self.telemetry.addData("MagDump", "Shooter off")
                self.InUse="Free"
            #Get real primevel
            if self.last_start != self.started:
                self.prime_velocity = velocity
            self.last_start = self.started


            if self.started:
                self.telemetry.addData("PrimeVel", self.prime_velocity)
                self.telemetry.addData("PrimeVel 95", self.prime_velocity*0.9)
                if velocity<self.prime_velocity*0.9:
                    self.shooter_intake().setPower(0)
                    self.telemetry.addData("MagDump", "Shooter intake deactivated")
                else:
                    self.shooter_intake().setPower(1)
                    self.telemetry.addData("MagDump", "Shooter intake activated")
                    self.telemetry.addData("Intake", self.shooter_intake().getVelocity())
                    if abs(self.shooter_intake().getVelocity()) < 50:
                        self.telemetry.addData("MagDump", "Reversing shooter")
                        self.shooter_intake().setPower(-1)
                        self.sleep(100)
                        
            #BallPickup
            BallPickup=self.phase_of(name="BallPickup")
            if BallPickup==1 and self.InUse=="Free":
                self.BallCollector().setPower(1)
                self.InUse="BallPickup"
                self.telemetry.addData("BallPickup", "Ball pickup active")
            elif BallPickup==0 and self.InUse=="BallPickup":
                self.BallCollector().setPower(0)
                self.InUse="Free"
                self.telemetry.addData("BallPickup", "Ball pickup off")
            
            #Fishing
            if self.gamepad1.dpad_down:
                self.chain_drop.setPosition(0.25)   
                self.EnteredFishing = True
                self.fishing.setPower(1)
                self.telemetry.addLine("Entered Fishing mode")
            elif self.gamepad1.dpad_up:
                self.fishing.setPower(-1)
            else:
                self.fishing.setPower(0)
            
            #ChainStop
            if self.gamepad1.leftBumperWasPressed() and self.EnteredFishing:
                self.chain_stop.setPosition(0.4)
                self.telemetry.addLine("Chain stop activated")

            #Climbing
            ServoMoves = self.phase_of("ClimbScaffold")
            if ServoMoves==1:
                self.ClimbUpper.setDirection(CRServo.Direction.FORWARD)
                self.telemetry.addData("Climb dir", "UP")
            else:
                self.ClimbUpper.setDirection(CRServo.Direction.REVERSE)
                self.telemetry.addData("Climb dir", "DOWN")
            self.ClimbUpper.setPower(self.gamepad1.left_trigger)
            
            #FixatorRelease
            if self.gamepad1.left_stick_button and not self.DidUseFixator:
                self.fixator_release.setPower(-1)
                self.sleep(1000)
                self.fixator_release.setPower(0)
                self.DidUseFixator=True
            #cyclePhase
            self.cyclePhase("MagDump", self.gamepad1.cross)
            self.cyclePhase("BallPickup", self.gamepad1.circle)
            self.cyclePhase(name="ClimbDirection", pressed=self.floattobool(self.gamepad1.right_trigger))
            self.cyclePhase(name="ClimbScaffold", pressed=self.gamepad1.dpad_left)

            #telemetry
            self.telemetry.update()
            