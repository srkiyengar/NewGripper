__author__ = 'srkiyengar'
# Significant joystick code or the basis of it comes from pygame.joystick sample code
import pygame



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


