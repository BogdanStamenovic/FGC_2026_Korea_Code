# Gicko robot code (FGC 2026)

Python translated to OnBot Java by [rev-vscode](https://github.com/BogdanStamenovic/rev-vscode).
Hardware configuration on the hub: `FGC2026-Incheon`.

| file | what |
|---|---|
| `main.py` | TeleOp **Main**. Controls are listed at the top of the file. |
| `calibration.py` | TeleOp **Calibration**: measures the drivetrain once, saves it on the hub; step 11 records the shooter's distance table. |
| `drive.py` | `OmniDrive`: X-drive mix, calibrated corrections, heading hold, odometry, `drive_cm` / `turn_to` for autonomous. |
| `drive_cal.py` | `DriveCal`: the saved numbers, `/sdcard/FIRST/settings/omni_calibration.txt`. |
| `shooter.py` | `Flywheel` (spin by power or ticks/s, latch the settled "prime" speed) and `RangeFinder` (the `sDmeassure` 2m distance sensor, median of 5). |
| `shooter_cal.py` | `ShooterCal`: every calibration shot, `/sdcard/FIRST/settings/shooter_calibration.txt`, and the scoring band per speed. |
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

## Calibrating the shooter (step 11)

Needs the REV 2m Distance Sensor configured on the hub as **`sDmeassure`**,
facing the goal wall. Put the robot as close to the wall as it can score
from. On the setup page choose the step back (default 20 cm), the number of
stops (6), and the speeds in ticks/s (1400 to 2200 in steps of 200; 2200 is
about what a fresh battery gives at full power, and the top speed is always
tested). The robot then, at every stop, spins the flywheel to each speed with
the hub's velocity PID, waits for it to settle, fires one ball on cross, and
asks: cross = in, circle = missed, triangle = shoot again, square = skip this
speed, share = end the run. Then it backs away one step and does it again.
After the second stop it checks the wall really got farther away; if not,
the "away" direction on the setup page is wrong.

The file keeps the raw shots (target speed, measured speed, distance, hit).
For each speed, the longest unbroken run of hits, plus half a step on each
side, is the distance band where that speed scores. Runs can be added to the
saved shots or start fresh.

In **Main**, after cross spins the shooter up, the flywheel's settled speed
picks a band (interpolated between the two tested speeds around it), and
gamepad 1 rumbles for as long as the distance sensor is inside it. Press
cross then. The rumble is advice: cross shoots from anywhere, and without the
sensor or a table Main runs exactly as before, minus the rumble.

The table is recorded with velocity control and one ball per shot, while
Main shoots at full power and feeds while the flywheel is at 90% or more of
its settled speed. The first ball out of Main matches the table best; later
balls in a burst leave a little slower.

## What is verified and what is not

Verified in the rev-vscode simulator and by compiling against the real SDK
11.2 jars: every OpMode translates and compiles, the button fixes, the
non-blocking fixator, wheel scaling, heading hold reacting to a turned hub,
calibration steps 1-3 end to end with the file saved and read back by Main,
step 4 with the hub rotated by script, step 6's flow (limp motors, distance
entry, the too-few-ticks check), step 9's square, and `JamGuard` against scripted jams (free running, cleared jam,
permanent jam, current spike, grinding, paused feed, loaded running).

Also in the simulator (26 Sep): step 11 end to end (3 stops x 3 speeds,
bands computed, file saved and read back), the "not getting farther" check,
step 10's square, Main rumbling only inside the band and stopping on cross,
and Main without `sDmeassure` configured. Everything also compiles against
the real SDK 11.2 jars.

Not verified: anything on the real robot. The simulator has motors on a
bench, no chassis, so the calibration *numbers* (and steps 5, 7, 8 as a whole)
can only be proven on the floor. Writing to `/sdcard/FIRST/settings/` has not
been confirmed on a real Control Hub yet; Calibration reads every save back
and says so on the Driver Hub if it did not stick.

The simulator has no balls and no flywheel load: it cannot show a shot's
flywheel dip (every test shot there reads "no shot seen"), and its shooter
runs at the bench free speed (~2800 t/s), not the robot's 2200. The
one-ball feed (stop once the flywheel dips 4%) and the JamGuard limits
loosened on 26 Sep are untested on the robot.
