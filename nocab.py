"""TeleOp nocab: Main with the omni-wheel calibration switched off.

Same controls and everything else as Main. The drive ignores
omni_calibration.txt (it is not even read) and runs the plain wheel mix, as
Testing's RAW page does: no wheel matching, no drift correction, no heading
hold. For when the calibration file is suspect or the robot drives worse
with it than without.
"""

from ftc.opmode import TeleOp
from main import Main


@TeleOp(name="nocab", group="pyftc")
class NoCab(Main):
    def use_calibration(self) -> bool:
        return False
