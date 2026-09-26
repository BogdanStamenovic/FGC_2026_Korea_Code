"""Gamepad test: shows which button the FTC SDK sees, by name, on both
gamepads. For finding out what extra buttons (M1/M2, back paddles) send: the
SDK only knows the standard buttons, so a controller reports those as one of
them, whichever its own software maps them to.

Press any button: it is listed while held, and the last 6 presses stay on
screen. Nothing moves.
"""

from ftc.hardware import Gamepad
from ftc.opmode import LinearOpMode, TeleOp


@TeleOp(name="Gamepad test", group="pyftc")
class GamepadTest(LinearOpMode):
    held1: str
    held2: str
    history: list[str]

    def runOpMode(self) -> None:
        self.held1 = ""
        self.held2 = ""
        self.history = []
        self.telemetry.addLine("Press START, then press buttons.")
        self.telemetry.update()
        self.waitForStart()
        while self.opModeIsActive():
            now1 = self.pressed(self.gamepad1)
            now2 = self.pressed(self.gamepad2)
            self.remember("gamepad 1", now1, self.held1)
            self.remember("gamepad 2", now2, self.held2)
            self.held1 = now1
            self.held2 = now2
            self.telemetry.addData("gamepad 1 held", now1)
            self.telemetry.addData("gamepad 2 held", now2)
            self.telemetry.addData("gamepad 1 sticks", self.sticks(self.gamepad1))
            self.telemetry.addData("gamepad 2 sticks", self.sticks(self.gamepad2))
            self.telemetry.addLine("")
            self.telemetry.addLine("last presses:")
            for line in self.history:
                self.telemetry.addLine("  " + line)
            self.telemetry.update()

    def remember(self, which: str, now: str, before: str) -> None:
        if now != "" and now != before:
            self.history.insert(0, which + ": " + now)
            if len(self.history) > 6:
                self.history.pop()

    def pressed(self, g: Gamepad) -> str:
        # PS names first: cross/circle/square/triangle are the same buttons as a/b/x/y.
        names: list[str] = []
        if g.a:
            names.append("cross (a)")
        if g.b:
            names.append("circle (b)")
        if g.x:
            names.append("square (x)")
        if g.y:
            names.append("triangle (y)")
        if g.dpad_up:
            names.append("dpad_up")
        if g.dpad_down:
            names.append("dpad_down")
        if g.dpad_left:
            names.append("dpad_left")
        if g.dpad_right:
            names.append("dpad_right")
        if g.left_bumper:
            names.append("left_bumper")
        if g.right_bumper:
            names.append("right_bumper")
        if g.left_stick_button:
            names.append("left_stick_button (L3)")
        if g.right_stick_button:
            names.append("right_stick_button (R3)")
        if g.back:
            names.append("share (back)")
        if g.start:
            names.append("options (start)")
        if g.guide:
            names.append("ps (guide)")
        if g.touchpad:
            names.append("touchpad")
        if g.left_trigger > 0.2:
            names.append(f"left_trigger {g.left_trigger:.2f}")
        if g.right_trigger > 0.2:
            names.append(f"right_trigger {g.right_trigger:.2f}")
        text = ""
        for n in names:
            if text != "":
                text = text + ", "
            text = text + n
        return text

    def sticks(self, g: Gamepad) -> str:
        return f"L {g.left_stick_x:+.2f} {g.left_stick_y:+.2f}   R {g.right_stick_x:+.2f} {g.right_stick_y:+.2f}"
