# Main: robot reference

Generated from hardware configuration "FGC2026-Incheon" on Gicko. Configuration fingerprint `c841abeba9d5c0ab` (`python -m pyftc config-fingerprint --config <config.xml>` on the same configuration reproduces it).

This is generated wholesale every time `Main.py`'s starter pack is spawned or updated. Unlike the `.py` file it carries no markers, so edit it freely, but don't expect an edit to survive the next regeneration.

## This robot

- Configuration name: `FGC2026-Incheon`
- Device name: `Gicko`
- RC app 11.2, SDK 11.2.0, OS 1.1.6

| Hub | Address | Firmware | Answered when generated |
|---|---|---|---|
| Expansion Hub 2 | 2 | 1.8.2 | yes |
| Control Hub | 173 | 1.8.2 | yes |

## Devices

### "Collector" -> `self.collector`

- Hub: Expansion Hub 2 (address 2), port 0
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 560 encoder ticks/rev
- 300 max RPM
- 20:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "shooter" -> `self.shooter`

- Hub: Expansion Hub 2 (address 2), port 1
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 560 encoder ticks/rev
- 300 max RPM
- 20:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "Climber" -> `self.climber`

- Hub: Expansion Hub 2 (address 2), port 2
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 560 encoder ticks/rev
- 300 max RPM
- 20:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "Fishing" -> `self.fishing`

- Hub: Expansion Hub 2 (address 2), port 3
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 288 encoder ticks/rev
- 137 max RPM
- 36.25:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "LB" -> `self.lb`

- Hub: Control Hub (address 173), port 0
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 560 encoder ticks/rev
- 300 max RPM
- 20:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "RB" -> `self.rb`

- Hub: Control Hub (address 173), port 1
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 560 encoder ticks/rev
- 300 max RPM
- 20:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "LF" -> `self.lf`

- Hub: Control Hub (address 173), port 2
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 560 encoder ticks/rev
- 300 max RPM
- 20:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "RF" -> `self.rf`

- Hub: Control Hub (address 173), port 3
- Python type: `DcMotor` (`com.qualcomm.robotcore.hardware.DcMotor`)
- 560 encoder ticks/rev
- 300 max RPM
- 20:1 gearing

Complete `DcMotor` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**DcMotor**

- `getMotorType() -> MotorConfigurationType` -- Returns the assigned type for this motor. If no particular motor type has been configured, then MotorConfigurationType#getUnspecifiedMotorType() will be returned. Note that the motor type for a given motor is initially assigned in the robot configuration user interface, though it may subsequently be modified using methods herein.
- `setMotorType(motorType: MotorConfigurationType)` -- Sets the assigned type of this motor. Usage of this method is very rare.
- `getController() -> DcMotorController` -- Returns the underlying motor controller on which this motor is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying motor controller on which this motor is situated.
- `setZeroPowerBehavior(zeroPowerBehavior: ZeroPowerBehavior)` -- Sets the behavior of the motor when a power level of zero is applied.
- `getZeroPowerBehavior() -> ZeroPowerBehavior` -- Returns the current behavior of the motor were a power level of zero to be applied.
- `setPowerFloat()` -- Sets the zero power behavior of the motor to ZeroPowerBehavior#FLOAT, then applies zero power to that motor. Note that the change of the zero power behavior to ZeroPowerBehavior#FLOAT remains in effect even following the return of this method. This is a breaking change in behavior from previous releases of the SDK. Consider, for example, the following code sequence:
- `getPowerFloat() -> bool` -- Returns whether the motor is currently in a float power level.
- `setTargetPosition(position: int)` -- Sets the desired encoder target position to which the motor should advance or retreat and then actively hold thereat. This behavior is similar to the operation of a servo. The maximum speed at which this advance or retreat occurs is governed by the power level currently set on the motor. While the motor is advancing or retreating to the desired taget position, #isBusy() will return true. Note that adjustment to a target position is only effective when the motor is in RunMode#RUN_TO_POSITION RunMode. Note further that, clearly, the motor must be equipped with an encoder in order for this mode to function properly.
- `getTargetPosition() -> int` -- Returns the current target encoder position for this motor.
- `isBusy() -> bool` -- Returns true if the motor is currently advancing or retreating to a target position.
- `getCurrentPosition() -> int` -- Returns the current reading of the encoder for this motor. The units for this reading, that is, the number of ticks per revolution, are specific to the motor/encoder in question, and thus are not specified here.
- `setMode(mode: RunMode)` -- Sets the current run mode for this motor
- `getMode() -> RunMode` -- Returns the current run mode for this motor

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "chainDrop" -> `self.chain_drop`

- Hub: Control Hub (address 173), port 0
- Python type: `Servo` (`com.qualcomm.robotcore.hardware.Servo`)

Complete `Servo` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**Servo**

- `MIN_POSITION: float` -- The minimum allowable position to which a servo can be moved
- `MAX_POSITION: float` -- The maximum allowable position to which a servo can be moved
- `getController() -> ServoController` -- Returns the underlying servo controller on which this servo is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying servo controller on which this motor is situated.
- `setDirection(direction: Direction)` -- Sets the logical direction in which this servo operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this servo is set as operating.
- `setPosition(position: float)` -- Sets the current position of the servo, expressed as a fraction of its available range. If PWM power is enabled for the servo, the servo will attempt to move to the indicated position.
- `getPosition() -> float` -- Returns the position to which the servo was last commanded to move. Note that this method does NOT read a position from the servo through any electrical means, as no such electrical mechanism is, generally, available.
- `scaleRange(min: float, max: float)` -- Scales the available movement range of the servo to be a subset of its maximum range. Subsequent positioning calls will operate within that subset range. This is useful if your servo has only a limited useful range of movement due to the physical hardware that it is manipulating (as is often the case) but you don't want to have to manually scale and adjust the input to #setPosition(double) each time. For example, if scaleRange(0.2, 0.8) is set; then servo positions will be scaled to fit in that range: setPosition(0.0) scales to 0.2 setPosition(1.0) scales to 0.8 setPosition(0.5) scales to 0.5 setPosition(0.25) scales to 0.35 setPosition(0.75) scales to 0.65

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "ChainStop" -> `self.chain_stop`

- Hub: Control Hub (address 173), port 1
- Python type: `Servo` (`com.qualcomm.robotcore.hardware.Servo`)

Complete `Servo` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**Servo**

- `MIN_POSITION: float` -- The minimum allowable position to which a servo can be moved
- `MAX_POSITION: float` -- The maximum allowable position to which a servo can be moved
- `getController() -> ServoController` -- Returns the underlying servo controller on which this servo is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying servo controller on which this motor is situated.
- `setDirection(direction: Direction)` -- Sets the logical direction in which this servo operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this servo is set as operating.
- `setPosition(position: float)` -- Sets the current position of the servo, expressed as a fraction of its available range. If PWM power is enabled for the servo, the servo will attempt to move to the indicated position.
- `getPosition() -> float` -- Returns the position to which the servo was last commanded to move. Note that this method does NOT read a position from the servo through any electrical means, as no such electrical mechanism is, generally, available.
- `scaleRange(min: float, max: float)` -- Scales the available movement range of the servo to be a subset of its maximum range. Subsequent positioning calls will operate within that subset range. This is useful if your servo has only a limited useful range of movement due to the physical hardware that it is manipulating (as is often the case) but you don't want to have to manually scale and adjust the input to #setPosition(double) each time. For example, if scaleRange(0.2, 0.8) is set; then servo positions will be scaled to fit in that range: setPosition(0.0) scales to 0.2 setPosition(1.0) scales to 0.8 setPosition(0.5) scales to 0.5 setPosition(0.25) scales to 0.35 setPosition(0.75) scales to 0.65

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "ShooterIntake" -> `self.shooter_intake`

- Hub: Control Hub (address 173), port 2
- Python type: `CRServo` (`com.qualcomm.robotcore.hardware.CRServo`)

Complete `CRServo` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**CRServo**

- `getController() -> ServoController` -- Returns the underlying servo controller on which this servo is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying servo controller on which this motor is situated.

**DcMotorSimple**

- `setDirection(direction: Direction)` -- Sets the logical direction in which this motor operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this motor is set as operating.
- `setPower(power: float)` -- Sets the power level of the motor, expressed as a fraction of the maximum possible power / speed supported according to the run mode in which the motor is operating. Setting a power level of zero will brake the motor
- `getPower() -> float` -- Returns the current configured power level of the motor.

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "FixatorRelease" -> `self.fixator_release`

- Hub: Control Hub (address 173), port 3
- Python type: `Servo` (`com.qualcomm.robotcore.hardware.Servo`)

Complete `Servo` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**Servo**

- `MIN_POSITION: float` -- The minimum allowable position to which a servo can be moved
- `MAX_POSITION: float` -- The maximum allowable position to which a servo can be moved
- `getController() -> ServoController` -- Returns the underlying servo controller on which this servo is situated.
- `getPortNumber() -> int` -- Returns the port number on the underlying servo controller on which this motor is situated.
- `setDirection(direction: Direction)` -- Sets the logical direction in which this servo operates.
- `getDirection() -> Direction` -- Returns the current logical direction in which this servo is set as operating.
- `setPosition(position: float)` -- Sets the current position of the servo, expressed as a fraction of its available range. If PWM power is enabled for the servo, the servo will attempt to move to the indicated position.
- `getPosition() -> float` -- Returns the position to which the servo was last commanded to move. Note that this method does NOT read a position from the servo through any electrical means, as no such electrical mechanism is, generally, available.
- `scaleRange(min: float, max: float)` -- Scales the available movement range of the servo to be a subset of its maximum range. Subsequent positioning calls will operate within that subset range. This is useful if your servo has only a limited useful range of movement due to the physical hardware that it is manipulating (as is often the case) but you don't want to have to manually scale and adjust the input to #setPosition(double) each time. For example, if scaleRange(0.2, 0.8) is set; then servo positions will be scaled to fit in that range: setPosition(0.0) scales to 0.2 setPosition(1.0) scales to 0.8 setPosition(0.5) scales to 0.5 setPosition(0.25) scales to 0.35 setPosition(0.75) scales to 0.65

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

### "imu" -> `self.imu`

- Hub: Control Hub (address 173), port 0
- Python type: `IMU` (`com.qualcomm.robotcore.hardware.IMU`)

Complete `IMU` method list, own class first then inherited, grouped by the class that declares each member (the `.py` file's comments only carry the first sentence of each javadoc - this is the whole thing):

**IMU**

- `initialize(parameters: Parameters) -> bool` -- Initializes the IMU with non-default settings.
- `resetYaw()` -- Resets the robot's yaw angle to 0. After calling this method, the reported orientation will be relative to the robot's position when this method was called, as if the robot was perfectly level right then. That is to say, the pitch and yaw will be ignored when this method is called.
- `getRobotYawPitchRollAngles() -> YawPitchRollAngles`
- `getRobotOrientation(reference: AxesReference, order: AxesOrder, angleUnit: AngleUnit) -> Orientation`
- `getRobotOrientationAsQuaternion() -> Quaternion`
- `getRobotAngularVelocity(angleUnit: AngleUnit) -> AngularVelocity`

**HardwareDevice**

- `getManufacturer() -> Manufacturer` -- Returns an indication of the manufacturer of this device.
- `getDeviceName() -> str` -- Returns a string suitable for display to the user as to the type of device. Note that this is a device-type-specific name; it has nothing to do with the name by which a user might have configured the device in a robot configuration.
- `getConnectionInfo() -> str` -- Get connection information about this device in a human readable format
- `getVersion() -> int` -- Version
- `resetDeviceConfigurationForOpMode()` -- Resets the device's configuration to that which is expected at the beginning of an OpMode. For example, motors will reset the their direction to 'forward'.
- `close()` -- Closes this device

## Control map

- "Collector": gamepad 1: left stick up/down
- "shooter": gamepad 1: right stick up/down
- "Climber": gamepad 1: right trigger forward, left trigger reverse
- "Fishing": gamepad 1: hold RB forward, hold LB reverse
- "LB": gamepad 1: hold D-pad up forward, hold D-pad down reverse
- "RB": gamepad 1: hold D-pad right forward, hold D-pad left reverse
- "LF": gamepad 1: hold Y forward, hold A reverse
- "RF": gamepad 1: hold B forward, hold X reverse
- "chainDrop": gamepad 2: hold RB / hold LB to move it
- "ChainStop": gamepad 2: hold D-pad up / hold D-pad down to move it
- "ShooterIntake": gamepad 2: left stick up/down
- "FixatorRelease": gamepad 2: hold D-pad right / hold D-pad left to move it
- "imu": gamepad 1 BACK resets the heading to 0

To change any of this: edit the code between `# ── pyftc:loop ──` and `# ── pyftc:loop:end ──` in `Main.py` directly (see "Anatomy" below for what else lives in there), or adjust `DRIVE_POWER`, `MECHANISM_POWER` and `SERVO_STEP` at the top of the class to change speed without touching which control does what.

## Anatomy of the generated file

Five marker regions, each a `# ── pyftc:<region> ──` / `# ── pyftc:<region>:end ──` pair of comments (docs/ARCHITECTURE.md, "Contract 4"):

| Region | What lives there | Runs at |
|---|---|---|
| `imports` | `from ftc.* import ...` lines the devices and controls need | import time |
| `hardware` | the per-hub, per-device description comments | (comment only) |
| `devices` | one `field: Type` class attribute per known device | class body |
| `init` | `hardwareMap.get(...)` lookups, direction/IMU setup, servo starting positions | INIT |
| `loop` | the gamepad control code for each device | START, every iteration |

Everything above `waitForStart()` runs once, when INIT is pressed. The `while self.opModeIsActive():` body runs every iteration from START until STOP.

**Do not delete the marker comments.** `starter-update` finds them by exact text match and refuses to touch the file at all if any is missing or duplicated - it will not guess where your code ends and generated code begins; it hands back the new code separately instead (as `block` in the CLI's JSON) for you to place by hand. Renaming fields, reordering devices, rewriting the control logic: all fine, none of it touches the marker lines themselves. Just leave those comment lines alone.

When the hardware configuration changes and you re-run *Spawn starter pack* on `Main.py` (or `starter-update` directly):

- a **new device** gets a field, a `hardwareMap` lookup, a gamepad control (if one is still free) and a hardware-comment line, each inserted immediately before its region's `:end` marker - after everything already there, never in the middle of it;
- a **removed device**'s field is never deleted - it gets a `# pyftc: no longer in the configuration` comment above it instead, so code you wrote using it still shows up as a diff instead of silently vanishing;
- a device that's merely **renamed or moved to a different port** is not detected as "the same device" - matching is by name only, so this looks like an old device removed and a new one added;
- descriptive comments about the old configuration (including a stale "no devices" banner on a configuration that used to be empty) are never rewritten either - if one no longer matches reality, that's the trade-off for never eating your edits.

## Recipes and limits

Adding a device by hand instead of re-spawning: declare a field, `self.hardwareMap.get(...)` it in `runOpMode`, and drive it however you like - [docs/MANUAL.md](docs/MANUAL.md), section 3 ("Adding any device: the recipe"), has the full walkthrough.

What Python the translator accepts and rejects, build/translation troubleshooting, autonomous, organizing code across files: all in [docs/MANUAL.md](docs/MANUAL.md) in the rev-vscode repository. This page is generated per-robot and intentionally doesn't repeat any of that.

