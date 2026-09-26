# Gicko robot code (FGC 2026)

Python translated to OnBot Java by [rev-vscode](https://github.com/BogdanStamenovic/rev-vscode).
Hardware configuration on the hub: `FGC2026-Incheon`.

| file | what |
|---|---|
| `main.py` | TeleOp **Main**. Controls are listed at the top of the file. |
| `calibration.py` | TeleOp **Calibration**: measures the drivetrain once, saves it on the hub. |
| `drive.py` | `OmniDrive`: X-drive mix, calibrated corrections, heading hold, odometry, `drive_cm` / `turn_to` for autonomous. |
| `drive_cal.py` | `DriveCal`: the saved numbers, `/sdcard/FIRST/settings/omni_calibration.txt`. |
| `jam.py` | `JamGuard`: detects a stuck intake, backs it out, gives up after 4 tries in 3 s. |
| `aftercare.py` | Empty after-match OpMode. |

## Calibrating the drive

Run **Calibration** on the Driver Hub, press START, and work down the menu.
Each step explains itself before anything moves and saves as soon as you
accept it; the file survives power cycles and every OpMode loads it at INIT.

1-2 need the robot **on blocks** (wheels in the air), 3-9 on the floor.
Step 1 now checks each wheel in both directions; a wheel that only runs one
way cannot pass the motor check.
Redo 2 after changing a motor or gearbox, 3-5 after moving the Control Hub,
6-8 after changing wheels or the floor surface. Steps 9 and 10 change
nothing: they drive a 60 cm and a 1 m square (forward, right, back, left,
strafing, no turning) so you can see how good the numbers are.

Until step 5 (Turn ramp) is saved, heading hold stays off: which way the
robot turns for +rotation is only known once it has been measured, and a
wrong guess would make heading hold spin the robot.

## Driving and the telemetry that explains it

Left stick moves (up = forward, sideways = strafe), right stick X turns.
While you drive with the turn stick released, heading hold steers the robot
back to where it pointed. Its correction only gets the power your stick
leaves free, plus at most 10% taken from your command
(`OmniDrive.CORRECTION_RESERVE`). Before 27 Sep it was mixed in first and
everything was scaled back to full power afterwards, so at full stick a
knock off heading slowed the whole robot to as little as 71%.

Main shows three lines for telling a code problem from a hardware one:
`Drive output` (how much of the stick reaches the wheels, and the heading
correction), `Battery` (now and lowest this match: open-loop power means
the robot is slower when the battery sags, e.g. while the shooter spins up)
and `Loop` (time per loop and the worst in the last second; inputs lag by
about that much).

## What is verified and what is not

Verified in the rev-vscode simulator and by compiling against the real SDK
11.2 jars: every OpMode translates and compiles, the button fixes, the
non-blocking fixator, wheel scaling, heading hold reacting to a turned hub,
calibration steps 1-3 end to end with the file saved and read back by Main,
step 4 with the hub rotated by script, step 6's flow (limp motors, distance
entry, the too-few-ticks check), step 9's square, and `JamGuard` against scripted jams (free running, cleared jam,
permanent jam, current spike, grinding, paused feed, loaded running).

Also in the simulator (27 Sep): step 10's square, the left-stick-move /
right-stick-turn mapping, heading hold at full stick taking 10% instead of
scaling the drive down, and the new telemetry. Everything also compiles
against the real SDK 11.2 jars.

Not verified: anything on the real robot. The simulator has motors on a
bench, no chassis, so the calibration *numbers* (and steps 5, 7, 8 as a whole)
can only be proven on the floor. Writing to `/sdcard/FIRST/settings/` has not
been confirmed on a real Control Hub yet; Calibration reads every save back
and says so on the Driver Hub if it did not stick.

The JamGuard limits loosened on 26 Sep are untested on the robot.
