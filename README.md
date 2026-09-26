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
| `shooter_cal.py` | `ShooterCal`: one proven distance per flywheel speed, `/sdcard/FIRST/settings/shooter_calibration.txt`. |
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
facing the goal wall. The setup page picks the speeds in ticks/s: 1700 (the
lowest that is probably usable) to 2200 (about what a fresh battery gives at
full power) in steps of 100, and whether to keep the saved speeds.

For each speed the flywheel is held there by the hub's velocity PID and you
drive (left stick move, right stick turn) to where you think it scores. Load
ONE ball and press cross: the intake runs for 2 s. Answer cross = in,
circle = missed, triangle = don't count it. A miss restarts the count, and
so does moving more than 5 cm from where the count started. After 5 in a row,
load 5 balls: the next cross is a burst, fed like Main (6 s, pausing while
the flywheel is under 90% of its settled speed). All 5 in saves that speed
with the median distance of the 10 shots, on the spot, and moves to the next
speed. dpad right/left skips to the next/previous speed, share ends.

`shooter_cal.py` keeps one line per speed: target, the speed the flywheel
really settled at, distance. In **Main**, after cross spins the shooter up,
its settled speed picks a distance (interpolated between the two saved
speeds around it) and gamepad 1 rumbles while the sensor reads within 5 cm
of it (`ShooterCal.TOLERANCE_CM`). Press cross then. The rumble is advice:
cross shoots from anywhere, and without the sensor or a table Main runs
exactly as before, minus the rumble.

The table is recorded with velocity control, Main shoots at full power, so
a burst in Main recovers a little slower between balls than the calibration
burst did.

## What is verified and what is not

Verified in the rev-vscode simulator and by compiling against the real SDK
11.2 jars: every OpMode translates and compiles, the button fixes, the
non-blocking fixator, wheel scaling, heading hold reacting to a turned hub,
calibration steps 1-3 end to end with the file saved and read back by Main,
step 4 with the hub rotated by script, step 6's flow (limp motors, distance
entry, the too-few-ticks check), step 9's square, and `JamGuard` against scripted jams (free running, cleared jam,
permanent jam, current spike, grinding, paused feed, loaded running).

Also in the simulator (27 Sep): step 11's manual flow (5 in a row, a miss
and a 12 cm move both restarting the count, the burst, the save and read
back, skipping a speed), the left-stick-move / right-stick-turn mapping in
Main and Calibration, step 10's square, Main rumbling only within 5 cm of
the table's distance and stopping on cross, and Main without `sDmeassure`
configured. Everything also compiles against the real SDK 11.2 jars.

Not verified: anything on the real robot. The simulator has motors on a
bench, no chassis, so the calibration *numbers* (and steps 5, 7, 8 as a whole)
can only be proven on the floor. Writing to `/sdcard/FIRST/settings/` has not
been confirmed on a real Control Hub yet; Calibration reads every save back
and says so on the Driver Hub if it did not stick.

The simulator has no balls and no flywheel load, and its shooter runs at
the bench free speed (~2800 t/s), not the robot's 2200. Whether 2 s of feed
fires one ball and 6 s fires five, and the JamGuard limits loosened on
26 Sep, are untested on the robot.
