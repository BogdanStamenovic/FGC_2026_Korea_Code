"""Shooter calibration: for each tested flywheel speed, one distance from the
goal wall where the Calibration OpMode's shooter step proved it scores (5
single balls in a row plus a 5-ball burst, all in, from one spot). Saved as
plain text on the hub.

File: /sdcard/FIRST/settings/shooter_calibration.txt. One line per speed:
    point=<target t/s>,<measured t/s>,<distance cm>
The measured speed is what the flywheel actually settled at; Main compares
its own settled speed ("prime") against that, not against the target.
Version-1 files (raw shot lines) are ignored: their "shot=" lines are unknown
keys here.

Main asks band_for(prime): the distance interpolated between the two speeds
around prime, +- TOLERANCE_CM.
"""

from ftc.io import AppUtil, File, ReadWriteFile


class ShooterCal:
    FILE_NAME: str = "shooter_calibration.txt"
    VERSION: int = 2
    # How far from a proven distance still counts as in range. The proof was
    # made from one spot, so this is a guess: widen it if the rumble is too
    # picky, narrow it if shots from the edge miss.
    TOLERANCE_CM: float = 5.0
    # A speed up to 5% outside the tested ones still uses the nearest point;
    # further out the table says nothing.
    EDGE_FRACTION: float = 0.05

    loaded: bool
    load_error: str
    # Sorted by measured speed, ascending.
    point_target: list[float]
    point_tps: list[float]
    point_cm: list[float]

    # band_for()'s answer.
    found_cm: float
    found_lo: float
    found_hi: float

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.loaded = False
        self.load_error = ""
        self.point_target = []
        self.point_tps = []
        self.point_cm = []
        self.found_cm = 0.0
        self.found_lo = 0.0
        self.found_hi = 0.0

    def count(self) -> int:
        return len(self.point_cm)

    def index_of(self, target: float) -> int:
        for k in range(len(self.point_target)):
            if self.point_target[k] == target:
                return k
        return -1

    def set_point(self, target: float, tps: float, cm: float) -> None:
        """Add a speed's distance, replacing an earlier one for the same target."""
        old = self.index_of(target)
        if old >= 0:
            self.point_target.pop(old)
            self.point_tps.pop(old)
            self.point_cm.pop(old)
        k = 0
        while k < len(self.point_tps) and self.point_tps[k] < tps:
            k = k + 1
        self.point_target.insert(k, target)
        self.point_tps.insert(k, tps)
        self.point_cm.insert(k, cm)

    def band_for(self, tps: float) -> bool:
        """Distance window (found_lo..found_hi, cm) where a flywheel settled at
        tps scores. False when the table has nothing for that speed."""
        n = len(self.point_tps)
        if n == 0:
            return False
        if tps <= self.point_tps[0]:
            return self.use_point(0, tps)
        if tps >= self.point_tps[n - 1]:
            return self.use_point(n - 1, tps)
        k = 0
        while self.point_tps[k + 1] < tps:
            k = k + 1
        f = (tps - self.point_tps[k]) / (self.point_tps[k + 1] - self.point_tps[k])
        self.set_found(self.point_cm[k] + f * (self.point_cm[k + 1] - self.point_cm[k]))
        return True

    def use_point(self, k: int, tps: float) -> bool:
        if abs(tps - self.point_tps[k]) > self.EDGE_FRACTION * self.point_tps[k]:
            return False
        self.set_found(self.point_cm[k])
        return True

    def set_found(self, cm: float) -> None:
        self.found_cm = cm
        self.found_lo = cm - self.TOLERANCE_CM
        self.found_hi = cm + self.TOLERANCE_CM

    # ------------------------------------------------------------------ file

    def file(self) -> File:
        return AppUtil.getInstance().getSettingsFile(self.FILE_NAME)

    def load(self) -> None:
        f: File = self.file()
        if not f.exists():
            return
        try:
            for line in ReadWriteFile.readFile(f).split("\n"):
                parts = line.strip().split("=")
                if len(parts) != 2 or parts[0] != "point":
                    continue
                v = parts[1].split(",")
                if len(v) != 3:
                    raise ValueError("bad point line '" + line + "'")
                self.set_point(float(v[0]), float(v[1]), float(v[2]))
            self.loaded = True
        except ValueError as e:
            # A corrupt file must not stop Main: no table, and say so.
            self.reset()
            self.load_error = "shooter table unreadable: " + str(e)

    def save(self) -> None:
        # str(), not f"{x:.1f}": String.format follows the hub's locale and
        # would write "1,5", which the comma-separated line then splits apart.
        text = "version=" + str(self.VERSION) + "\n"
        for k in range(len(self.point_cm)):
            text = text + "point=" + str(self.point_target[k]) + "," + str(self.point_tps[k]) + "," + str(self.point_cm[k]) + "\n"
        ReadWriteFile.writeFile(self.file(), text)
        self.loaded = True
