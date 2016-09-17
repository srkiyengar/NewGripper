# New Gripper
This is a variation of the model used in Gripper.
A joystick measurement is used to drive the velocity of the servo. The variation between Gripper and NewGripper is that the most recent displacement is used to update the goal position. Also, the key commands from the Joystick will be replaced by keyboard commands to get ready for arduino based miniature joystick that can mount on a mold attached to the casing of the Reflex casing.

At the neurobotics lab at University of Waterloo, we are attempting to collect data associated with human grasping actions while picking up of objects (like the ones in the YCB model set). The setup consists of a Reflex_SF gripper (in future also Reflex Takktile) from Righthandrobotics controlled through a Logitech Extreme joystick, an NDI Polaris capturing the coordinates and the quaternion vectors based on rigid body reflectors attached to the Reflex, and an image processing mechanism to capture the position of the YCB object while gripping.

Control of Reflex_SF: The control of the Reflex_SF is accomplished through sending commands to the 4 Dynamixel servos. A USB2Dynamixel interface is built in to the Reflex_SF. Dynamixel has a detailed instruction set for MX-28, the servo used in Reflex. The actuator protocol description is detailed. An implementation of this interface was made available (see acknowledgement in dynamixel.py).
