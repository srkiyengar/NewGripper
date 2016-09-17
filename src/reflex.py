__author__ = 'srkiyengar'

import dynamixel
import logging




MOVE_TICKS = 130
MOVE_TICKS_SERVO4 = 70
POS_ERROR = 20


CALIBRATION_TICKS = 50


MAX_FINGER_MOVEMENT = 2100
MAX_PRESHAPE_MOVEMENT = 1200

MAX_SPEED = 600 # A max speed of 1023 is allowed

# This logger is setup in the main python script
my_logger = logging.getLogger("My_Logger")
LOG_LEVEL = logging.DEBUG



# Since Fingers start from 1 to 4, list and tuples will have index 0 left unused.

class reflex_sf():
    '''The class manages the calibration and movement of the fingers for pinch and grasp
    '''
    def __init__(self, usb_channel = '/dev/ttyUSB0', baudrate = 57600):
        dyn = dynamixel.USB2Dynamixel_Device(usb_channel, baudrate)

        # The l_limit corresponds to initial rest position of the fingers. It cannot go lower for 1 and 3 and higher for
        # 2 and 4.  The servo is only inolved in spreading the fingers 1 and 2 apart or closer
        # The upper limit is something that can be set to when the aperture of the fingers 1,2 and 3 = zero or less
        # A visual calibration is essential and the associated servo position is the l_limits
        l_limits = [0,13920,16740,15600, 14980]
        u_limits = [0,0,0,0,0]

        # The l_limits are saved in a file
        try:
            fp = open("calibration","r")
        except IOError:
            raise IOError("Unable to open calibration file")

        cal_str = fp.readline()
        j = 0
        for i in cal_str.split(','):
            l_limits[j] = int(i)
            j = j + 1
        fp.close()

        my_logger.info("Rest Positions F1-{} F2-{} F3-{} F4 {}".format
                       (l_limits[1],l_limits[2],l_limits[3],l_limits[4]))
        self.finger = []
        self.finger.append(0) # finger starts with 1. Inserting 0 at the first list position

        for i in range(1,5,1):
            try:
                # using the USB2Dynamixel object try to send commands to each and receive information
                j= dynamixel.Robotis_Servo(dyn, i,"MX" )
            except:
                raise RuntimeError('Connection to Servo failure for servo number', i,'\n')
            current_pos = j.read_current_position()
            speed = MAX_SPEED
            j.set_speed(speed)


            if i==1:
                joint_state = 1
                u_limits[i] = l_limits[i] + MAX_FINGER_MOVEMENT
            elif i==2:
                joint_state = -1
                u_limits[i] = l_limits[i] - MAX_FINGER_MOVEMENT
            elif i==3:
                joint_state = 1
                u_limits[i] = l_limits[i] + MAX_FINGER_MOVEMENT
            elif i==4:
                joint_state = -1
                u_limits[i] = l_limits[i] - MAX_PRESHAPE_MOVEMENT

            # Current position - Actual servo position determined while servo is not moving
            # Goal Position is where we want the servo to move - it starts at rest position which should be reset @ start
            # Current Location may also be updated by reading but these reads cannot be done by waiting for the servo


            finger_parameters = {"servo":j, "initial_position": current_pos,
                                 "moving_speed":speed,
                                 "lower_limit":l_limits[i],"upper_limit":u_limits[i],"rotation":joint_state,
                                 "CP":current_pos, "CL":current_pos, "GP":current_pos}
            self.finger.append(finger_parameters)

    def get_palm_rest_position(self):   #Returns a list of current lower limit
        rest_limits = [0,0,0,0,0]
        for i in range(1,5,1):
            rest_limits[i] = self.finger[i]["lower_limit"]
        return rest_limits

    def set_palm_rest_position(self,set_limits):
        for i in range(1,5,1):
            val = set_limits[i]
            self.finger[i]["lower_limit"] = val
            self.finger[i]["GP"] = val
            self.finger[i]["CP"] = val
            self.finger[i]["CL"] = val
            if i==1:
                self.finger[i]["upper_limit"] = set_limits[i] + MAX_FINGER_MOVEMENT
            elif i==2:
                self.finger[i]["upper_limit"] = set_limits[i] - MAX_FINGER_MOVEMENT
            elif i==3:
                self.finger[i]["upper_limit"] = set_limits[i] + MAX_FINGER_MOVEMENT
            elif i==4:
                self.finger[i]["upper_limit"] = set_limits[i] - MAX_PRESHAPE_MOVEMENT

            x = self.finger[i]["lower_limit"]
            y = self.finger[i]["upper_limit"]
            my_logger.debug('Finger {} Lower Limit {} -- Upper Limit {}'.format(i,x,y))
        return 1

    def get_palm_current_location(self): #Returns a list of "CL" from palm object
        current_location = [0,0,0,0,0]
        for i in range(1,5,1):
            current_location[i] = self.finger[i]["CL"]
        return current_location

    def get_palm_current_position(self): #Returns a list of current position from palm object
        current_position = [0,0,0,0,0]
        for i in range(1,5,1):
            current_position[i] = self.finger[i]["CP"]
        return current_position

    def read_palm_servo_positions(self):  #Reads from Servos 1-4  after ensuring that servos are not moving
        current_location = [0,0,0,0,0]
        for i in range(1,5,1):
            current_location[i] = self.servo_current_position(i)
        return current_location

    def servo_current_position(self,id):           # checks if the servo is moving
        while (self.finger[id]["servo"].is_moving()):
            pass
        p = self.finger[id]["servo"].read_current_position()
        return p

    # New goal position is checked to see if it is within limits. Otherwise limits become the new position
    def is_finger_within_limit(self, id, new_position):
        '''
        :param id: id is the servo id 1,2,3,4
        :param new_position: it is the current value and this will get updated
        :return:the same new position is returned.
        '''
        ll = self.finger[id]["lower_limit"]
        ul = self.finger[id]["upper_limit"]
        rotation_mode = self.finger[id]["rotation"]
        if rotation_mode == 1:
            if ul >= new_position >= ll:
                return new_position
            else:
                old_position = new_position
                if new_position > ul:
                    new_position = ul
                elif new_position < ll:
                    new_position = ll
                my_logger.debug('Finger {} set to {} instead of {}'.format(id,new_position,old_position))
                return new_position
        elif rotation_mode == -1:
           if ll>=new_position >= ul:
               return new_position
           else:
               old_position = new_position
               if new_position > ll:
                    new_position = ll
               elif new_position < ul:
                    new_position = ul
               my_logger.debug('Finger {} set to {} instead of {}'.format(id,new_position,old_position))
               return new_position
        else:
            my_logger.debug("Finger{} joint rotation mode: {} unknown",format(rotation_mode))
            return 0

    def set_servo_speed(self,new_speed):    # set new speed
        for i in range(1,5,1):
            p = self.finger[i]["servo"].set_speed(new_speed)
        return

    def get_servo_speed(self):
        S = [0,0,0,0,0]
        same = 1
        for i in range(1,5,1):
            speed = self.finger[1]["servo"].read_speed()
            S[i] = speed
            if (i==1):
                S[0] = speed
            if(i>1 and speed != S[0]):
                same = 0

        if same==1:
            return speed
        else:
            return 0

    def get_servo_present_speed(self):      #reading from address 0x26
        ps = [0,0,0,0,0]
        same = 1
        for i in range(1,5,1):
            vel = self.finger[1]["servo"].read_present_speed()
            ps[i] = vel
            if (i==1):
                ps[0] = vel
            if(i>1 and vel != ps[0]):
                same = 0

        if same==1:
            return vel
        else:
            return 0

    # How much should each finger(1,2,3) move? and whether aperture is opening (grip = -1) the aperture (grip = 1)
    # Fingers 1,2, and 3 have approx. total of 1200 to get from open to close the aperture
    # The Reflex is setup as multi-turn mode with Default Resolution Divider
    # Goal position is set to where we want the finger position, individually.
    # This function affects the aperture of the precision grip

    def grip_fingers(self, move_by, grip):
        F = [0,0,0,0,0]
        if grip == 1:
            my_logger.info('Tighten by {} '.format(move_by))
        elif grip == -1:
            my_logger.info('Loosen by {} '.format(move_by))

        for i in range(1,4,1):  # servos 1,2,3
            p = self.finger[i]["GP"]
            q = self.finger[i]["rotation"]
            q *= grip
            move_to = p + q*move_by
            move_to = self.is_finger_within_limit(i,move_to)        #Checking for limits
            if move_to > 0:
                self.finger[i]["servo"].set_goal_position(move_to)
                self.finger[i]["GP"] = move_to     # new_position when out of bounds will be modified.
                F[i] = move_to
            else:
                F[i] = p
                my_logger.info\
                    ('Outside Limit Finger{} - Denied: Move From Position {} to Position {}'.format(id,p,move_to))
        return F # returning where it the fingers are supposed to move - others are zero

    # This is for servo 4 which changes the seperation between 1 and 3
    def space_finger1_and_finger2(self, move_by, grip):
        if grip == 1:
            my_logger.info('Spread finger 1 and 2 by {}'.format(move_by))
        elif grip == -1:
            my_logger.info('Bring finger 1 and 2 closer by {}'.format(move_by))
        P = self.move_finger_delta(4,grip,move_by)
        return P

    # This is used to modify the spacing between Fingers 1 and 3 (servo 4)
    # It moves any servo by any "increment" value.
    def move_finger_delta(self, id, move_direction,increment): # move_direction +1 = finger closing; -1 = finger opening
        p = self.finger[id]["GP"]
        q = self.finger[id]["rotation"]
        q *= move_direction
        new_position = p + q*increment
        move_to = self.is_finger_within_limit(id,new_position)
        if move_to > 0:
            self.finger[id]["servo"].set_goal_position(move_to) # return data to make the program wait
            self.finger[id]["GP"] = move_to     # new_position when out of bounds will be modified. Therefore
            return move_to
        else:
            my_logger.info\
                ('Outside Limit Finger{} - Denied: Move From Position {} to Position {}'.format(id,p,new_position))
            return 0

    # For calibration purposes
    # The manual move is by a set value
    def manual_move_finger(self,servo_id, move_direction):
        increment = CALIBRATION_TICKS
        self.manual_move_finger_delta(servo_id,move_direction,increment)
        p = self.servo_current_position(servo_id)   #After the move
        self.finger[servo_id]["GP"] = p
        self.finger[servo_id]["CP"] = p
        self.finger[servo_id]["CL"] = p

    # This
    def manual_move_finger_delta(self, id, move_direction,increment): # direction +1 = finger closing; -1 = finger opening
        p = self.servo_current_position(id)         #Before the move
        my_logger.debug('Finger {} MoveFrom: {}'.format(id,p))
        q = self.finger[id]["rotation"]
        q *= move_direction
        new_position = p + q*increment
        if self.is_finger_within_limit(id,new_position) == 0:
            # We need to allow manual move to exceed limits but are logging the warning
            my_logger.debug('Out of range warning!!!: Finger {} MoveFrom: {} to MoveTo: {}'.format(id,p, new_position))
        my_logger.debug('Finger {} MoveTo: {}'.format(id,new_position))
        self.finger[id]["servo"].set_goal_position(new_position)
        return

    def move_to_rest_position(self):        # checks where the servos are and sets goal positions = starting values
        current_position = self.read_palm_servo_positions()
        for i in range(1,5,1):
            rest_position = self.finger[i]["lower_limit"]
            my_logger.info("Moving  Servo: {} From: {} to Rest position: {}".format(i, current_position[i],rest_position))
            self.finger[i]["servo"].set_goal_position(rest_position)
            self.finger[i]["GP"] = rest_position
            self.finger[i]["CP"] = rest_position
            self.finger[i]["CL"] = rest_position
        return

    def get_rest_position(self):
        F = []
        F.append(0)
        for i in range(1,5,1):
            rest_position = self.finger[i]["lower_limit"]
            F.append(rest_position)
        return F

    def get_max_position(self):
        F=[]
        F.append(0)
        for i in range(1,5,1):
            max_position = self.finger[i]["upper_limit"]
            F.append(max_position)
        return F

    def move_to_goal_position(self,gp):
        for i in range(1,5,1):
            my_logger.info("Moving Servo: {} to Goal position: {}".format(i, gp[i]))
            # check if it is within limit
            self.is_finger_within_limit(i,gp[i])
            self.finger[i]["servo"].set_goal_position(gp[i])
            self.finger[i]["GP"] = gp[i]
        return

    def move_fingers(self,aperture_disp, pre_shape_disp):
        # calculating new goal positions
        aperture_disp = aperture_disp*MOVE_TICKS
        for i in range(1, 4, 1):      # only setting servo 1, 2, 3 for aperture change
            value = self.finger[i]["GP"]
            new_value = int(value + (aperture_disp*self.finger[i]["rotation"]))
            np = self.is_finger_within_limit(i, new_value)
            if np > 0:      # np > 1 is the valid gp when outside limit, np will be set to limit value of the servo
                my_logger.info("Moving Servo: {} to Goal position: {}".format(i, np))
                self.finger[i]["servo"].set_goal_position(np)
                self.finger[i]["GP"] = np
            else:
                raise RuntimeError('servo finger joint rotation error\n')

        value = self.finger[4]["GP"]
        new_value = int(value + (pre_shape_disp*self.finger[4]["rotation"]*MOVE_TICKS_SERVO4))
        np = self.is_finger_within_limit(4, new_value)
        if np > 0:      # np > 1 is the valid gp when outside limit, np will be set to limit value of the servo
            my_logger.info("Moving Servo: {} to Goal position: {}".format(i, np))
            self.finger[4]["servo"].set_goal_position(np)
            self.finger[4]["GP"] = np
        else:
            raise RuntimeError('servo finger joint rotation error\n')
        return

class joy_reflex_controller:
    def __init__(self, my_joy,grabber):
        self.controller = my_joy
        self.palm = grabber
        self.buttons = [0,0,0,0,0,0,0,0,0,0,0,0]  # 12 buttons 0 to 11
        self.hat_position = "E"
        self.Axes = [0.00,0.00,0.00,0.00]   # Displacement of 4 Axes

    def set_button_press(self, button):
        self.buttons[button] = 1
        self.process_button_actions()

    def set_button_release(self,button):
        self.buttons[button] = 0

    def reset_button_press(self,button):
        self.buttons[button] = 0

    def process_button_actions(self):  # Act based on Buttons
        if self.buttons[11] == 1:
            sid = 3
            grip = 1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(11)
        elif self.buttons[10] == 1:
            sid = 3
            grip = -1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(10)
        elif self.buttons[9] == 1:
            sid = 2
            grip = 1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(9)
        elif self.buttons[8] == 1:
            sid = 2
            grip = -1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(8)
        elif self.buttons[7] == 1:
            sid = 1
            grip = 1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(7)
        elif self.buttons[6] == 1:
            sid = 1
            grip = -1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(6)
        elif self.buttons[3] == 1:
            sid = 4
            grip = 1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(3)
        elif self.buttons[2] == 1:
            sid = 4
            grip = -1
            self.palm.manual_move_finger(sid,grip)
            self.reset_button_press(2)
        elif self.buttons[1] == 1:
            pass    #moved to gripper.py
        elif self.buttons[0] == 1:
            fingers = self.palm.read_palm_servo_positions()
            self.reset_button_press(0)
            my_logger.info("Current Finger Positions F1-{} F2-{} F3-{} F4-{}".format
                    (fingers[1],fingers[2],fingers[3],fingers[4]))
        elif self.buttons[4] and self.buttons[5]:
            my_logger.info("New Finger positions - calibration")
            try:
                fp = open("calibration","w")
            except IOError:
                raise IOError ("Unable to open calibration file")

            new_limits = self.palm.read_palm_servo_positions()
            self.palm.set_palm_rest_position(new_limits)
            self.reset_button_press(4)
            self.reset_button_press(5)
            my_logger.info("Calibration - New Rest Positions F1-{} F2-{} F3-{} F4 {}".format
                    (new_limits[1],new_limits[2],new_limits[3],new_limits[4]))
            s = str(new_limits)
            nes = s[1:]     # Remove [
            ges = nes[:-1]  # Remove ]
            fp.write(ges)   # write the remaining string
            fp.close()

    def update_calibration(self):
        my_logger.info("New Finger positions - calibration")
        try:
            fp = open("calibration","w")
        except IOError:
            raise IOError ("Unable to open calibration file")

        new_limits = self.palm.read_palm_servo_positions()
        self.palm.set_palm_rest_position(new_limits)
        my_logger.info("Calibration - New Rest Positions F1-{} F2-{} F3-{} F4 {}".format
                    (new_limits[1],new_limits[2],new_limits[3],new_limits[4]))
        s = str(new_limits)
        nes = s[1:]     # Remove [
        ges = nes[:-1]  # Remove ]
        fp.write(ges)   # write the remaining string
        fp.close()
        return new_limits