__author__ = 'srkiyengar'
# Significant joystick code or the basis of it comes from pygame.joystick sample code
import pygame
import serial
import sys



JOY_DEADZONE_A0 = 0.2
JOY_DEADZONE_A1 = 0.1


# Before invoking this class pygame.init() needs to be called


class ExtremeProJoystick():
    def __init__( self):
        # Initialize the joysticks
        pygame.joystick.init()
        self.joystick_count = pygame.joystick.get_count()
        if self.joystick_count == 0:
            raise RuntimeError('No Joystick not found\n')
        else:
            My_joystick = pygame.joystick.Joystick(0)
            name = My_joystick.get_name()
            if ("Logitech Extreme 3D" in name):
                self.name = name
                My_joystick.init()
                self.axes = My_joystick.get_numaxes()
                self.buttons = My_joystick.get_numbuttons()
                self.hats = My_joystick.get_numhats()
                self.joystick= My_joystick
                self.min_val = [-JOY_DEADZONE_A0,-JOY_DEADZONE_A1,-0.5,-0.5]
                self.max_val = [JOY_DEADZONE_A0,JOY_DEADZONE_A1,0.5,0.5]
            else:
                raise RuntimeError('Logitech Extreme #D Joystick not found\n')

    def get_displacement(self,k):
        """
        This function has to get the displacement of the Joystick axis where k is the axis indicator
        :param k is the Axis identifier:
        :return: is a float which represents displacement magnitude and direction.
        """
        return self.joystick.get_axis(k)


    def get_displacement_outside_deadzone(self,k,displacement):
        """
        This function zeroes any displacement in the deadzone
        :param k is the Axis identifier:
        :param displacement is the joystick displacement in axis k
        :return: is the displacement magnitude and direction after zeroing deadzone
        """
        if displacement > 0:
            if displacement <= self.max_val[k]:
                displacement = 0    # ignoring deadzone
        elif displacement < 0:
            if displacement >= self.min_val[k]:
                displacement = 0    # ignoring deadzone
        return displacement



    def get_button_pressed(self, my_event):
        button_number = my_event.dict['button']    # from pygame.event
        return button_number

    def get_button_released(self, my_event):
        button_number = my_event.dict['button']    # from pygame.event
        return button_number

    def get_hat_movement(self,my_event):
        Hat = my_event.dict['value']
        if Hat[0] < 0:
            return "R"  #Right
        if Hat[0] > 0:
            return "L"  #Left
        if Hat[1] < 0:
            return "U"  #Up
        if Hat[1] > 0:
            return "D"  #Down

        return "E"      #No movement

class Thumbstick():
    def __init__(self,port='/dev/ttyACM0', baud=9600):
        self.axes = 2
        self.hats = 0
        self.name = "Arduino Thumstick"
        self.buttons = 1
        self.button_press = 0
        self.x = 0.0
        self.y = 0.0
        self.min_val = [-JOY_DEADZONE_A0,-JOY_DEADZONE_A1]
        self.max_val = [JOY_DEADZONE_A0,JOY_DEADZONE_A1]
        try:
            self.ser = serial.Serial(port,baud,timeout=.0001)   # 100 micro second to read timeout
        except IOError as e:
            print "I/O error: {}".format(e)
            self.connect = False
            raise
        else:
            self.connect = True

    def read_byte(self):
        try:
            my_byte = self.ser.read(1)   # Will try to read one byte within timeout second; return is str type
        except IOError as e:
            print "I/O error in read_byte: {}".format(e)
            raise
        except:
            print "Unexpected error in read_byte: {}", sys.exc_info()[0]
            raise
        else:
            return my_byte

    def get_response(self,cmd):
        response = []
        try:
            self.ser.write(chr(cmd))
        except IOError as e:
            print "I/O error in get_response: {}".format(e)
            raise
        except:
            print "Unexpected error in get_response: {}", sys.exc_info()[0]
            raise
        else:
            keep_reading = True
            while (keep_reading):
                try:
                    this_byte = self.read_byte()
                except IOError as e:
                    print "I/O error: {}".format(e)
                    raise
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
                else:
                    if (this_byte == '\n'):
                        keep_reading = False
                        response.remove('\r')
                        response.append(this_byte)
                    else:
                        response.append(this_byte)

            value = int("".join(response))
            # The thumb stick 0-1023 in X and Y axis
            # The rest position is 515, 501 (500 or 501, this keeps flipping)
            if cmd == 0:
                if value >= 0:
                    return value/508.0
                else:
                    return value/515.0
            elif cmd == 1:
                if value >=0:
                    return value/522.0
                else:
                    if value == -1:         # this is a hack as value moves back and forth between 500 and 501
                        value = 0           # We don't this to considered as joystick movement.
                    return value/501.0
            elif cmd == 255:
                return value

    def get_displacement(self,k):
        return self.get_response(k)
        
    def get_displacement_outside_deadzone(self,k,displacement):
        """
        This function zeroes any displacement in the deadzone
        :param k is the Axis identifier:
        :param displacement is the joystick displacement in axis k
        :return: is the displacement magnitude and direction after zeroing deadzone
        """
        if displacement > 0:
            if displacement <= self.max_val[k]:
                displacement = 0    # ignoring deadzone
        elif displacement < 0:
            if displacement >= self.min_val[k]:
                displacement = 0    # ignoring deadzone
        return displacement





