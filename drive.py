"""OmniDrive: the X-drive (four omni wheels at the corners, 45 degrees) with the
Calibration OpMode's corrections applied, plus odometry and blocking moves for
autonomous.

Commands are in the driver's frame: fwd +1 = forward, strafe +1 = right,
rot +1 = what pushing the turn stick right does. The wheel mix is the one the
TeleOp has always used; only the corrections are new.

What each correction fixes (DriveCal has the measured numbers):
  wheel matching   every wheel gets the same speed for the same command
                   (a weak motor otherwise curves the robot)
  scaling          when sticks combine past full power, all four wheels are
                   scaled together so the direction is kept (the SDK would clip
                   each wheel on its own and bend it)
  drift feedforward  the turning a straight drive still does (weight, carpet)
  heading hold     IMU closed loop: with the turn stick released, the robot
                   keeps pointing where it pointed
"""

import math

from ftc.hardware import DcMotor, DcMotorEx, DcMotorSimple, HardwareMap, IMU, RevHubOrientationOnRobot
from ftc.navigation import AngleUnit
from ftc.opmode import LinearOpMode
from ftc.util import ElapsedTime, Range
from drive_cal import DriveCal


class OmniDrive:
    WHEEL_NAMES: list[str] = ["LF", "RF", "LB", "RB"]
    WHEEL_LONG: list[str] = ["front-left", "front-right", "back-left", "back-right"]

    STICK_DEADBAND: float = 0.05
    # Heading hold: the robot is steered back at (error / HOLD_TAU_S) deg/s, so an
    # error closes with a ~0.3 s time constant. Power per deg/s comes from the
    # calibrated turn_kv, so the gain follows the robot instead of being guessed.
    HOLD_TAU_S: float = 0.3
    HOLD_MAX_DPS: float = 120.0
    HOLD_MAX_POWER: float = 0.4
    HOLD_ERROR_DEADBAND_DEG: float = 0.5
    # After the turn stick is released the robot is still rotating; the new
    # heading to hold is captured once it has (nearly) stopped.
    HOLD_CAPTURE_DPS: float = 15.0
    HOLD_CAPTURE_MAX_MS: float = 300.0
    # Autonomous moves: power per cm (or per degree) of remaining error, on top
    # of the static-friction power that gets the robot moving at all.
    AUTO_KP_CM: float = 0.03
    AUTO_KP_DEG: float = 0.008
    AUTO_DONE_CM: float = 1.0
    AUTO_DONE_DEG: float = 1.5

    cal: DriveCal
    motors: list[DcMotorEx]
    imu: IMU
    # Mix: wheel power = FWD[i]*fwd + STR[i]*strafe + ROT[i]*rot, wheels LF,RF,LB,RB.
    # The three patterns are orthogonal, so the same numbers also read the
    # encoders back into forward/strafe/rotation (odometry).
    FWD: list[float]
    STR: list[float]
    ROT: list[float]
    use_corrections: bool
    v_common: float

    last_raw_yaw: float
    unwrapped_yaw: float
    yaw_timer: ElapsedTime
    last_pos: list[float]
    x_cm: float
    y_cm: float
    heading_deg: float

    hold_enabled: bool
    hold_active: bool
    hold_target: float
    turn_release: ElapsedTime

    def __init__(self, hw: HardwareMap, cal: DriveCal) -> None:
        self.cal = cal
        self.FWD = [-1.0, -1.0, 1.0, 1.0]
        self.STR = [-1.0, 1.0, -1.0, 1.0]
        self.ROT = [1.0, -1.0, -1.0, 1.0]
        self.motors = []
        for name in self.WHEEL_NAMES:
            self.motors.append(hw.get(DcMotorEx, name))
        # Same directions the TeleOp always had: the mix above depends on them.
        self.motors[0].setDirection(DcMotorSimple.Direction.FORWARD)
        self.motors[1].setDirection(DcMotorSimple.Direction.REVERSE)
        self.motors[2].setDirection(DcMotorSimple.Direction.REVERSE)
        self.motors[3].setDirection(DcMotorSimple.Direction.FORWARD)
        for m in self.motors:
            m.setMode(DcMotor.RunMode.RUN_WITHOUT_ENCODER)
            m.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)
        self.imu = hw.get(IMU, "imu")
        self.use_corrections = True
        self.v_common = self.common_speed()
        self.hold_enabled = True
        self.hold_active = False
        self.hold_target = 0.0
        self.turn_release = ElapsedTime()
        self.yaw_timer = ElapsedTime()
        self.last_pos = [0.0, 0.0, 0.0, 0.0]
        self.x_cm = 0.0
        self.y_cm = 0.0
        self.heading_deg = 0.0
        self.last_raw_yaw = 0.0
        self.unwrapped_yaw = 0.0

    # ------------------------------------------------------------------ IMU

    def init_imu(self) -> None:
        self.init_imu_as(self.cal.imu_logo, self.cal.imu_usb)

    def init_imu_as(self, logo: str, usb: str) -> None:
        self.imu.initialize(IMU.Parameters(RevHubOrientationOnRobot(self.logo_from(logo), self.usb_from(usb))))

    @staticmethod
    def logo_from(name: str) -> RevHubOrientationOnRobot.LogoFacingDirection:
        if name == "DOWN":
            return RevHubOrientationOnRobot.LogoFacingDirection.DOWN
        if name == "FORWARD":
            return RevHubOrientationOnRobot.LogoFacingDirection.FORWARD
        if name == "BACKWARD":
            return RevHubOrientationOnRobot.LogoFacingDirection.BACKWARD
        if name == "LEFT":
            return RevHubOrientationOnRobot.LogoFacingDirection.LEFT
        if name == "RIGHT":
            return RevHubOrientationOnRobot.LogoFacingDirection.RIGHT
        return RevHubOrientationOnRobot.LogoFacingDirection.UP

    @staticmethod
    def usb_from(name: str) -> RevHubOrientationOnRobot.UsbFacingDirection:
        if name == "UP":
            return RevHubOrientationOnRobot.UsbFacingDirection.UP
        if name == "DOWN":
            return RevHubOrientationOnRobot.UsbFacingDirection.DOWN
        if name == "BACKWARD":
            return RevHubOrientationOnRobot.UsbFacingDirection.BACKWARD
        if name == "LEFT":
            return RevHubOrientationOnRobot.UsbFacingDirection.LEFT
        if name == "RIGHT":
            return RevHubOrientationOnRobot.UsbFacingDirection.RIGHT
        return RevHubOrientationOnRobot.UsbFacingDirection.FORWARD

    def raw_yaw(self) -> float:
        return self.imu.getRobotYawPitchRollAngles().getYaw(AngleUnit.DEGREES)

    def raw_yaw_rate(self) -> float:
        return self.imu.getRobotAngularVelocity(AngleUnit.DEGREES).zRotationRate

    def yaw_rate(self) -> float:
        """deg/s, CCW positive, scale-corrected."""
        return self.raw_yaw_rate() * self.cal.imu_scale

    def raw_unwrapped(self) -> float:
        """Raw IMU yaw with the +-180 wrap removed; call once per loop (update does)."""
        yaw = self.raw_yaw()
        self.unwrapped_yaw = self.unwrapped_yaw + self.wrap180(yaw - self.last_raw_yaw)
        self.last_raw_yaw = yaw
        return self.unwrapped_yaw

    @staticmethod
    def wrap180(deg: float) -> float:
        while deg > 180.0:
            deg = deg - 360.0
        while deg <= -180.0:
            deg = deg + 360.0
        return deg

    # ------------------------------------------------------------------ encoders

    def raw_position(self, i: int) -> float:
        return float(self.motors[i].getCurrentPosition())

    def position(self, i: int) -> float:
        return self.raw_position(i) * self.cal.enc_sign[i]

    def velocity(self, i: int) -> float:
        return self.motors[i].getVelocity() * self.cal.enc_sign[i]

    def combine(self, pattern: list[float], values: list[float]) -> float:
        total = 0.0
        for i in range(4):
            total = total + pattern[i] * values[i]
        return total / 4.0

    def positions(self) -> list[float]:
        out: list[float] = []
        for i in range(4):
            out.append(self.position(i))
        return out

    def velocities(self) -> list[float]:
        out: list[float] = []
        for i in range(4):
            out.append(self.velocity(i))
        return out

    # ------------------------------------------------------------------ odometry

    def start(self) -> None:
        """Call at START: heading and position become 0 here."""
        self.imu.resetYaw()
        self.last_raw_yaw = 0.0
        self.unwrapped_yaw = 0.0
        self.yaw_timer.reset()
        self.last_pos = self.positions()
        self.x_cm = 0.0
        self.y_cm = 0.0
        self.heading_deg = 0.0
        self.hold_active = False

    def update(self) -> None:
        """Once per loop: heading from the IMU, position from the encoders.
        x is forward and y is left of where the robot stood at start()."""
        before = self.heading_deg
        raw = self.raw_unwrapped()
        self.heading_deg = raw * self.cal.imu_scale - self.cal.imu_drift * self.cal.imu_scale * self.yaw_timer.seconds()
        pos = self.positions()
        delta: list[float] = []
        for i in range(4):
            delta.append(pos[i] - self.last_pos[i])
        self.last_pos = pos
        d_fwd = self.combine(self.FWD, delta) / self.cal.ticks_per_cm_fwd
        d_left = -self.combine(self.STR, delta) / self.cal.ticks_per_cm_str
        h = math.radians((before + self.heading_deg) / 2.0)
        self.x_cm = self.x_cm + d_fwd * math.cos(h) - d_left * math.sin(h)
        self.y_cm = self.y_cm + d_fwd * math.sin(h) + d_left * math.cos(h)

    def heading(self) -> float:
        return self.heading_deg

    # ------------------------------------------------------------------ output

    def common_speed(self) -> float:
        """Fastest speed (ticks/s) every wheel can reach in both directions: the
        weakest wheel sets the pace, so full stick is still a straight line."""
        if not self.cal.has("wheels"):
            return 0.0
        v = 1e9
        for i in range(4):
            v = min(v, self.cal.kv_pos[i] * (1.0 - self.cal.ks_pos[i]))
            v = min(v, self.cal.kv_neg[i] * (1.0 - self.cal.ks_neg[i]))
        return v

    def wheel_power(self, i: int, w: float) -> float:
        """Power for wheel i to turn at fraction w of the common speed."""
        if abs(w) < 0.001:
            return 0.0
        if not self.use_corrections or self.v_common <= 0.0:
            return w
        if w > 0:
            return self.cal.ks_pos[i] + w * self.v_common / self.cal.kv_pos[i]
        return -self.cal.ks_neg[i] + w * self.v_common / self.cal.kv_neg[i]

    def set_raw(self, i: int, power: float) -> None:
        self.motors[i].setPower(Range.clip(power, -1.0, 1.0))

    def stop(self) -> None:
        for m in self.motors:
            m.setPower(0.0)

    def set_float(self, floating: bool) -> None:
        for m in self.motors:
            if floating:
                m.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.FLOAT)
            else:
                m.setZeroPowerBehavior(DcMotor.ZeroPowerBehavior.BRAKE)

    def drive(self, fwd: float, strafe: float, rot: float) -> None:
        if self.use_corrections:
            rot = rot + self.cal.drift_fwd * fwd + self.cal.drift_str * strafe
        w: list[float] = []
        biggest = 1.0
        for i in range(4):
            w.append(self.FWD[i] * fwd + self.STR[i] * strafe + self.ROT[i] * rot)
            biggest = max(biggest, abs(w[i]))
        for i in range(4):
            self.set_raw(i, self.wheel_power(i, w[i] / biggest))

    # ------------------------------------------------------------------ heading hold

    def heading_correction(self, target: float) -> float:
        """Rotation power that steers the heading toward target (degrees).
        Zero until the Turn ramp step has measured which way +rotation turns:
        with the sign guessed wrong this would be positive feedback and spin
        the robot."""
        if not self.cal.has("ramp"):
            return 0.0
        err = self.wrap180(target - self.heading_deg)
        if abs(err) < self.HOLD_ERROR_DEADBAND_DEG:
            return 0.0
        want_dps = Range.clip(err / self.HOLD_TAU_S, -self.HOLD_MAX_DPS, self.HOLD_MAX_DPS)
        # turn_kv is signed (deg/s per unit rot), so the division also picks the
        # direction: no separate "which way is CCW" flag to get wrong.
        return Range.clip(want_dps / self.cal.turn_kv, -self.HOLD_MAX_POWER, self.HOLD_MAX_POWER)

    def teleop(self, fwd: float, strafe: float, turn: float) -> None:
        """Stick driving. While the driver turns, the turn stick is obeyed as is;
        once it is released the heading is captured and held, but only while
        the robot is being driven (so a parked robot doesn't fight a push)."""
        moving = abs(fwd) > self.STICK_DEADBAND or abs(strafe) > self.STICK_DEADBAND
        rot = turn
        if abs(turn) > self.STICK_DEADBAND:
            self.hold_active = False
            self.turn_release.reset()
        elif not self.hold_enabled or not moving:
            self.hold_active = False
            rot = 0.0
        else:
            if not self.hold_active:
                settled = abs(self.yaw_rate()) < self.HOLD_CAPTURE_DPS
                if settled or self.turn_release.milliseconds() > self.HOLD_CAPTURE_MAX_MS:
                    self.hold_target = self.heading_deg
                    self.hold_active = True
            if self.hold_active:
                rot = self.heading_correction(self.hold_target)
            else:
                rot = 0.0
        self.drive(fwd, strafe, rot)

    # ------------------------------------------------------------------ autonomous

    def drive_cm(self, op: LinearOpMode, fwd_cm: float, left_cm: float, max_power: float, timeout_s: float) -> bool:
        """Move by (fwd_cm, left_cm) relative to the robot's current pose,
        keeping the current heading. Blocks; returns False on timeout or STOP."""
        self.update()
        h0 = self.heading_deg
        hr = math.radians(h0)
        tx = self.x_cm + fwd_cm * math.cos(hr) - left_cm * math.sin(hr)
        ty = self.y_cm + fwd_cm * math.sin(hr) + left_cm * math.cos(hr)
        timer = ElapsedTime()
        while op.opModeIsActive() and timer.seconds() < timeout_s:
            self.update()
            ex = tx - self.x_cm
            ey = ty - self.y_cm
            h = math.radians(self.heading_deg)
            e_fwd = ex * math.cos(h) + ey * math.sin(h)
            e_left = -ex * math.sin(h) + ey * math.cos(h)
            dist = math.sqrt(e_fwd * e_fwd + e_left * e_left)
            if dist < self.AUTO_DONE_CM:
                self.stop()
                return True
            speed = min(max_power, self.cal.turn_ks + dist * self.AUTO_KP_CM)
            self.drive(speed * e_fwd / dist, -speed * e_left / dist, self.heading_correction(h0))
        self.stop()
        return False

    def turn_to(self, op: LinearOpMode, target_deg: float, max_power: float, timeout_s: float) -> bool:
        """Turn in place to target_deg (CCW positive, 0 = heading at start())."""
        timer = ElapsedTime()
        while op.opModeIsActive() and timer.seconds() < timeout_s:
            self.update()
            err = self.wrap180(target_deg - self.heading_deg)
            if abs(err) < self.AUTO_DONE_DEG and abs(self.yaw_rate()) < 10.0:
                self.stop()
                return True
            mag = min(max_power, self.cal.turn_ks + abs(err) * self.AUTO_KP_DEG)
            # +rot turns the robot the way turn_kv's sign says
            ccw = 1.0
            if self.cal.turn_kv < 0:
                ccw = -1.0
            if err < 0:
                mag = -mag
            self.drive(0.0, 0.0, mag * ccw)
        self.stop()
        return False
