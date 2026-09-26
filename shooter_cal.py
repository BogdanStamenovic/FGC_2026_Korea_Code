"""Shooter calibration: every test shot the Calibration OpMode's shooter step
fired, saved as plain text on the hub, and the scoring bands derived from them.

File: /sdcard/FIRST/settings/shooter_calibration.txt. One line per shot:
    shot=<target t/s>,<measured t/s>,<distance cm>,<1 hit / 0 miss>
Raw shots are stored, not the bands, so a better way to read them later needs
no new shots; the file can be pulled with adb and opened in a spreadsheet.

Bands: for each target speed, the shots are sorted by distance and the longest
unbroken run of hits is where that speed scores, widened by half the step
between stops on both sides. Main asks band_for(prime) with the flywheel's
settled speed and gets a distance window, interpolated between the two tested
speeds around it.
"""

from ftc.io import AppUtil, File, ReadWriteFile


class ShooterCal:
    FILE_NAME: str = "shooter_calibration.txt"
    VERSION: int = 1
    # A speed up to 5% outside the tested ones still uses the nearest band;
    # further out the table says nothing.
    EDGE_FRACTION: float = 0.05

    loaded: bool
    load_error: str
    interval_cm: float
    shot_target: list[float]
    shot_tps: list[float]
    shot_cm: list[float]
    shot_hit: list[bool]

    # Derived by build(), one entry per tested target speed, ascending speed.
    level_target: list[float]
    level_tps: list[float]
    level_has_band: list[bool]
    level_lo: list[float]
    level_hi: list[float]
    level_hits: list[int]
    level_shots: list[int]

    # band_for()'s answer.
    found_lo: float
    found_hi: float

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.loaded = False
        self.load_error = ""
        self.interval_cm = 20.0
        self.shot_target = []
        self.shot_tps = []
        self.shot_cm = []
        self.shot_hit = []
        self.found_lo = 0.0
        self.found_hi = 0.0
        self.build()

    def add(self, target: float, tps: float, cm: float, hit: bool) -> None:
        self.shot_target.append(target)
        self.shot_tps.append(tps)
        self.shot_cm.append(cm)
        self.shot_hit.append(hit)

    def count(self) -> int:
        return len(self.shot_cm)

    def hits(self) -> int:
        n = 0
        for h in self.shot_hit:
            if h:
                n = n + 1
        return n

    # ------------------------------------------------------------------ bands

    def build(self) -> None:
        self.level_target = []
        self.level_tps = []
        self.level_has_band = []
        self.level_lo = []
        self.level_hi = []
        self.level_hits = []
        self.level_shots = []
        targets: list[float] = []
        for t in self.shot_target:
            k = 0
            while k < len(targets) and targets[k] < t:
                k = k + 1
            if k == len(targets) or targets[k] != t:
                targets.insert(k, t)
        for t in targets:
            self.build_level(t)

    def build_level(self, target: float) -> None:
        # This speed's shots, sorted by distance.
        cms: list[float] = []
        hit: list[bool] = []
        tps_sum = 0.0
        hits = 0
        for i in range(len(self.shot_cm)):
            if self.shot_target[i] != target:
                continue
            tps_sum = tps_sum + self.shot_tps[i]
            if self.shot_hit[i]:
                hits = hits + 1
            k = 0
            while k < len(cms) and cms[k] <= self.shot_cm[i]:
                k = k + 1
            cms.insert(k, self.shot_cm[i])
            hit.insert(k, self.shot_hit[i])
        best_start = -1
        best_len = 0
        run_start = -1
        for k in range(len(cms)):
            if hit[k]:
                if run_start < 0:
                    run_start = k
                if k - run_start + 1 > best_len:
                    best_len = k - run_start + 1
                    best_start = run_start
            else:
                run_start = -1
        pad = self.interval_cm / 2.0
        self.level_target.append(target)
        self.level_tps.append(tps_sum / len(cms))
        self.level_hits.append(hits)
        self.level_shots.append(len(cms))
        if best_start < 0:
            self.level_has_band.append(False)
            self.level_lo.append(0.0)
            self.level_hi.append(0.0)
        else:
            self.level_has_band.append(True)
            self.level_lo.append(cms[best_start] - pad)
            self.level_hi.append(cms[best_start + best_len - 1] + pad)

    def band_for(self, tps: float) -> bool:
        """Distance window (found_lo..found_hi, cm) where a flywheel settled at
        tps scores. False when the table has nothing for that speed."""
        n = len(self.level_tps)
        if n == 0:
            return False
        if tps <= self.level_tps[0]:
            return self.use_level(0, tps)
        if tps >= self.level_tps[n - 1]:
            return self.use_level(n - 1, tps)
        k = 0
        while self.level_tps[k + 1] < tps:
            k = k + 1
        if self.level_has_band[k] and self.level_has_band[k + 1]:
            f = (tps - self.level_tps[k]) / (self.level_tps[k + 1] - self.level_tps[k])
            self.found_lo = self.level_lo[k] + f * (self.level_lo[k + 1] - self.level_lo[k])
            self.found_hi = self.level_hi[k] + f * (self.level_hi[k + 1] - self.level_hi[k])
            return True
        # Next to a speed that never scored: only trust a band right beside it.
        if tps - self.level_tps[k] < self.level_tps[k + 1] - tps:
            return self.use_level(k, tps)
        return self.use_level(k + 1, tps)

    def use_level(self, k: int, tps: float) -> bool:
        if not self.level_has_band[k]:
            return False
        if abs(tps - self.level_tps[k]) > self.EDGE_FRACTION * self.level_tps[k]:
            return False
        self.found_lo = self.level_lo[k]
        self.found_hi = self.level_hi[k]
        return True

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
                if len(parts) != 2:
                    continue
                if parts[0] == "interval_cm":
                    self.interval_cm = float(parts[1])
                elif parts[0] == "shot":
                    v = parts[1].split(",")
                    if len(v) != 4:
                        raise ValueError("bad shot line '" + line + "'")
                    self.add(float(v[0]), float(v[1]), float(v[2]), v[3] == "1")
            self.loaded = True
        except ValueError as e:
            # A corrupt file must not stop Main: no bands, and say so.
            self.reset()
            self.load_error = "shooter table unreadable: " + str(e)
        self.build()

    def save(self) -> None:
        # str(), not f"{x:.1f}": String.format follows the hub's locale and
        # would write "1,5", which the comma-separated line then splits apart.
        text = "version=" + str(self.VERSION) + "\n"
        text = text + "interval_cm=" + str(self.interval_cm) + "\n"
        for i in range(len(self.shot_cm)):
            hit = "1" if self.shot_hit[i] else "0"
            text = text + "shot=" + str(self.shot_target[i]) + "," + str(self.shot_tps[i]) + "," + str(self.shot_cm[i]) + "," + hit + "\n"
        ReadWriteFile.writeFile(self.file(), text)
        self.loaded = True
        self.build()
