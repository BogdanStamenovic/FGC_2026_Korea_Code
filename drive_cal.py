"""Drive calibration: every number the Calibration OpMode measures, saved as plain
text on the hub so it survives power cycles. Main and any autonomous load it at
INIT through OmniDrive.

File: /sdcard/FIRST/settings/omni_calibration.txt, one `key=value` per line,
lists comma-separated, wheel order LF,RF,LB,RB. Unknown keys are ignored and
missing keys keep their defaults, so an older file still loads after a new
field is added. Delete the file (or use Calibration's reset) to start over.
"""

from ftc.io import AppUtil, File, ReadWriteFile


class DriveCal:
    FILE_NAME: str = "omni_calibration.txt"
    VERSION: int = 1

    # Which steps have been accepted, e.g. "motors,wheels,imu". See Calibration.STEP_KEYS.
    done: str
    # Did a file load? False on a fresh hub; the defaults below are then in use.
    loaded: bool
    load_error: str

    # Step "motors": +1, or -1 for an encoder that counts against its motor.
    enc_sign: list[float]
    # Step "wheels", measured on blocks, per wheel and per direction:
    # velocity (ticks/s) = kv * (power - ks). kv 0 means not measured.
    ks_pos: list[float]
    ks_neg: list[float]
    kv_pos: list[float]
    kv_neg: list[float]
    # Step "imu": hub mounting and gyro drift at rest (deg/s, raw IMU units).
    imu_logo: str
    imu_usb: str
    imu_drift: float
    # Step "spin": true angle / IMU angle, and encoder rotation ticks per true
    # degree (sign included: CCW positive, like the IMU).
    imu_scale: float
    ticks_per_deg: float
    # Step "ramp", turning in place on the floor: rotation power where the robot
    # starts to move, and deg/s per unit of rotation power above it (signed: the
    # sign says which way +rotation turns the robot).
    turn_ks: float
    turn_kv: float
    # Steps "fwd" / "strafe": encoder ticks per cm, slip included (signed).
    ticks_per_cm_fwd: float
    ticks_per_cm_str: float
    # Step "drift": rotation power per unit of forward / strafe command that
    # cancels the turning the robot does by itself when driving straight.
    drift_fwd: float
    drift_str: float

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Back to uncalibrated defaults (does not touch the file)."""
        self.done = ""
        self.loaded = False
        self.load_error = ""
        self.enc_sign = [1.0, 1.0, 1.0, 1.0]
        self.ks_pos = [0.0, 0.0, 0.0, 0.0]
        self.ks_neg = [0.0, 0.0, 0.0, 0.0]
        self.kv_pos = [0.0, 0.0, 0.0, 0.0]
        self.kv_neg = [0.0, 0.0, 0.0, 0.0]
        self.imu_logo = "UP"
        self.imu_usb = "FORWARD"
        self.imu_drift = 0.0
        self.imu_scale = 1.0
        # Defaults are geometry guesses (90 mm omni wheels, 560 ticks/rev as the
        # SDK reports, wheels at 45 degrees); only good enough to not be absurd
        # before the robot is calibrated.
        self.ticks_per_deg = -10.0
        self.turn_ks = 0.08
        self.turn_kv = -250.0
        self.ticks_per_cm_fwd = 14.0
        self.ticks_per_cm_str = 14.0
        self.drift_fwd = 0.0
        self.drift_str = 0.0

    def has(self, step: str) -> bool:
        for s in self.done.split(","):
            if s == step:
                return True
        return False

    def mark(self, step: str) -> None:
        if self.has(step):
            return
        if self.done == "":
            self.done = step
        else:
            self.done = self.done + "," + step

    def done_count(self) -> int:
        if self.done == "":
            return 0
        return len(self.done.split(","))

    def file(self) -> File:
        return AppUtil.getInstance().getSettingsFile(self.FILE_NAME)

    def load(self) -> None:
        f: File = self.file()
        if not f.exists():
            return
        try:
            for line in ReadWriteFile.readFile(f).split("\n"):
                parts = line.strip().split("=")
                if len(parts) == 2:
                    self.set_value(parts[0], parts[1])
            self.loaded = True
        except ValueError as e:
            # A corrupt file must not stop the robot from driving: fall back to
            # defaults and say so on telemetry.
            self.reset()
            self.load_error = "calibration file unreadable, using defaults: " + str(e)

    def set_value(self, key: str, value: str) -> None:
        if key == "done":
            self.done = value
        elif key == "enc_sign":
            self.enc_sign = self.parse_list(value)
        elif key == "ks_pos":
            self.ks_pos = self.parse_list(value)
        elif key == "ks_neg":
            self.ks_neg = self.parse_list(value)
        elif key == "kv_pos":
            self.kv_pos = self.parse_list(value)
        elif key == "kv_neg":
            self.kv_neg = self.parse_list(value)
        elif key == "imu_logo":
            self.imu_logo = value
        elif key == "imu_usb":
            self.imu_usb = value
        elif key == "imu_drift":
            self.imu_drift = float(value)
        elif key == "imu_scale":
            self.imu_scale = float(value)
        elif key == "ticks_per_deg":
            self.ticks_per_deg = float(value)
        elif key == "turn_ks":
            self.turn_ks = float(value)
        elif key == "turn_kv":
            self.turn_kv = float(value)
        elif key == "ticks_per_cm_fwd":
            self.ticks_per_cm_fwd = float(value)
        elif key == "ticks_per_cm_str":
            self.ticks_per_cm_str = float(value)
        elif key == "drift_fwd":
            self.drift_fwd = float(value)
        elif key == "drift_str":
            self.drift_str = float(value)

    def parse_list(self, value: str) -> list[float]:
        parts = value.split(",")
        if len(parts) != 4:
            raise ValueError("expected 4 values, got '" + value + "'")
        out: list[float] = []
        for p in parts:
            out.append(float(p))
        return out

    def join(self, values: list[float]) -> str:
        return str(values[0]) + "," + str(values[1]) + "," + str(values[2]) + "," + str(values[3])

    def save(self) -> None:
        # str(), not f"{x:.5f}": String.format follows the hub's locale and would
        # write "1,5" on a comma-decimal locale, which parse_list then splits apart.
        text = "version=" + str(self.VERSION) + "\n"
        text = text + "done=" + self.done + "\n"
        text = text + "enc_sign=" + self.join(self.enc_sign) + "\n"
        text = text + "ks_pos=" + self.join(self.ks_pos) + "\n"
        text = text + "ks_neg=" + self.join(self.ks_neg) + "\n"
        text = text + "kv_pos=" + self.join(self.kv_pos) + "\n"
        text = text + "kv_neg=" + self.join(self.kv_neg) + "\n"
        text = text + "imu_logo=" + self.imu_logo + "\n"
        text = text + "imu_usb=" + self.imu_usb + "\n"
        text = text + "imu_drift=" + str(self.imu_drift) + "\n"
        text = text + "imu_scale=" + str(self.imu_scale) + "\n"
        text = text + "ticks_per_deg=" + str(self.ticks_per_deg) + "\n"
        text = text + "turn_ks=" + str(self.turn_ks) + "\n"
        text = text + "turn_kv=" + str(self.turn_kv) + "\n"
        text = text + "ticks_per_cm_fwd=" + str(self.ticks_per_cm_fwd) + "\n"
        text = text + "ticks_per_cm_str=" + str(self.ticks_per_cm_str) + "\n"
        text = text + "drift_fwd=" + str(self.drift_fwd) + "\n"
        text = text + "drift_str=" + str(self.drift_str) + "\n"
        ReadWriteFile.writeFile(self.file(), text)
        self.loaded = True

    def wipe(self) -> None:
        f: File = self.file()
        if f.exists():
            f.delete()
        self.reset()
