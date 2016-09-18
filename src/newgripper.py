__author__ = 'srkiyengar'

import pygame
import logging
import logging.handlers
from datetime import datetime
import reflex
import screen_print as sp
import joystick as js
import threading
import time

POS_ERROR = 20

#logger
LOG_LEVEL = logging.DEBUG
LOG_FILENAME = 'NewGripper' + datetime.now().strftime('%Y-%m-%d---%H:%M:%S')

# Define some colors
BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)

SCAN_RATE = 20                    #1 (one) second divided by scan rate is the loop checking if the main program should stop


change_aperture = 0.0
change_pre_shape = 0.0


# Setting the maximum cycle rate for the two threads 1)joystick loop and 2) servo command to move gripper
joy_loop_rate = 1000    # in microsecond
reflex_loop_rate = 16000    # in microsecond



last_time = datetime.now()
my_lock = threading.Lock()      # shared variables between the two threads are accessed through a lock

reflex_command_loop = True      # servo command thread loop control
joy_measurement_loop = True     # joystick loop control
joy_moved = False               # This is to restrict logging to logger only when there is a change in displacement


def stop_joy_loop():
    '''
    This will set the control to false and the joy thread will stop
    :return:
    '''
    global joy_measurement_loop
    joy_measurement_loop = False


def stop_reflex_loop():
    '''
    This will set the control to false and the Reflex servo command thread will stop
    :return:
    '''
    global reflex_command_loop
    reflex_command_loop = False


def update_joy_displacement(my_joy, e2):
    '''
    Displacement of Logitech Extreme 3D Joystick Axis 0 and 1 are updated into the joy_disp list at the rate set by
    'joy_loop_rate'
    :param my_joy: to get the displacement of Axis 0 (pre-shape) and 1 (aperture) palm: Reflex servo and e2: event
    communication between main and the threads especially for calibrating the joystick.
    :return: None
    '''
    last_joy_time = last_time
    counter = 1
    global joy_moved, change_aperture, change_pre_shape
    while joy_measurement_loop:
        e2.wait()       # This is used to pause the thread in case we want to calibrate the gripper
        present_time = datetime.now()
        delta_t = present_time - last_joy_time
        delta_t = delta_t.seconds*1000000 + delta_t.microseconds

        if delta_t < joy_loop_rate:
            delay = joy_loop_rate - delta_t
            delay = delay/1000000.0
            time.sleep(delay)

        measurement_time = datetime.now()
        axis_x = my_joy.get_displacement(0)  # Axis 0 - preshape displacement
        axis_y = my_joy.get_displacement(1)   # Axis 1 - Aperture displacement

        if axis_x != 0 or axis_y != 0:
            my_logger.info('Joystick Thread Counter: {} Time: {} Aperture Disp. {} Preshape Disp. {}'.
                            format(counter, str(measurement_time)[17:],axis_y,axis_x))

            with my_lock:
                joy_moved = True        # This is a flag to indicate Joystick is displaced from rest position.
                change_aperture = axis_y
                change_pre_shape = axis_x

            my_logger.info('Joy displacement flag is {} '.format(joy_moved))
            counter += 1

        last_joy_time = present_time


def move_reflex_to_goal_positions(palm,e2):
    '''
    This is to move the Reflex to joy_disp position at the rate set by
    'reflex_loop_rate'
    :type e2: event object
    :param palm: This is the reflex object in the main e2: event communication between main and the threads especially
    for calibrating the joystick.
    :return:
    '''
    counter = 1
    global last_time, joy_moved
    last_reflex_time = last_time

    while reflex_command_loop:
        e2.wait()       # This is used to pause the thread in case we want to calibrate the gripper
        present_time = datetime.now()
        delta_t = present_time - last_reflex_time
        delta_t = delta_t.seconds*1000000 + delta_t.microseconds

        if (delta_t < reflex_loop_rate):
            delay = reflex_loop_rate - delta_t
            delay = delay/1000000.0
            time.sleep(delay)

        with my_lock:
            aper_disp = change_aperture
            pre_disp = change_pre_shape
            move_servo = joy_moved

        command_time = datetime.now()

        if move_servo:
            my_logger.info('Thread Reflex Counter: {} - Time: {} Aperture disp {} Pre-shape disp'.
                           format(counter, command_time, aper_disp,pre_disp))
            # Sending the displacement to move_fingers in reflex.py to process
            palm.move_fingers(aper_disp,pre_disp)


            with my_lock:
                joy_moved = False
                my_logger.info('Thread Reflex - Resetting Joy Displacement Flag to {}'.format(joy_moved))

        counter += 1
        last_reflex_time = present_time
    my_logger.info('Exit Reflex thread')

if __name__ == '__main__':

    # Set up a logger with output level set to debug; Add the handler to the logger
    my_logger = logging.getLogger("My_Logger")
    my_logger.setLevel(LOG_LEVEL)
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=6000000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    # end of logfile preparation Log levels are debug, info, warn, error, critical

    #Create Palm object
    palm = reflex.reflex_sf() # Reflex object ready
    my_logger.info('Reflex_SF object created')

    for i in range(1,5,1):
        lowest_position = palm.finger[i]["lower_limit"]
        highest_position = palm.finger[i]["upper_limit"]
        init_position = palm.finger[i]["initial_position"]


        my_logger.info('--- Finger {}:'.format(i))
        my_logger.info('       Lower Limit Position --- {}'.format(lowest_position))
        my_logger.info('       Upper Limit Position --- {}'.format(highest_position))
        my_logger.info('       Initial Position {}'.format(init_position))

        calibrate = False

        if (i == 1 or i == 3):
            a = lowest_position - POS_ERROR
            b= highest_position + POS_ERROR
            if a >= init_position or init_position >= b:
                my_logger.info('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'\
                               .format(i,init_position,lowest_position,highest_position))
                print('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'.format(\
                    i,init_position,lowest_position,highest_position))
                #calibrate = 1
        elif (i == 2):
            a = lowest_position + POS_ERROR
            b = highest_position - POS_ERROR
            if a <= init_position or init_position <= b:
                my_logger.info('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'\
                               .format(i,init_position,lowest_position,highest_position))
                print('Servo {} Initial Position {} not between Lower Limit {} and Upper Limit {}'.format(\
                    i,init_position,lowest_position,highest_position))
                #calibrate = 1

        # calibration is a must after every start.

    pygame.init()
    # Set the width and height of the screen [width,height]
    size = [500, 700]
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Reflex_SF JoyStick Movements")

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()

    # for print in Pygame screen object
    textPrint = sp.TextPrint()

    # Joystick Values
    my_joy = js.ExtremeProJoystick()
    my_controller = reflex.joy_reflex_controller(my_joy,palm)

    # Event to pause the thread
    e2 = threading.Event()
    e2.set()    #Flag is set to allow the thread move_reflex_to_goal_positions to run

    calibrate = False

    while calibrate is False:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                button = my_joy.get_button_pressed(event)
                my_logger.info("Button {} pressed".format(button))
                if button in (2,3,6,7,8,9,10,11):
                    my_controller.set_button_press(button)
                elif button == 1:   #silver button on the right facing the buttons
                    gp_servo = my_controller.update_calibration()
                    calibrate = True
                else:
                    my_logger.info("Button {} press ignored before calibration".format(button))
            elif event.type == pygame.JOYBUTTONUP:
                button = my_joy.get_button_released(event)
                my_logger.info("Button {} Released".format(button))
                if button in (2,3,6,7,8,9,10,11):
                    my_controller.set_button_release(button)
                else:
                    my_logger.info("Button {} press ignored before calibration".format(button))
            else:
                pass # ignoring other non-logitech joystick event types


    # preparing the two threads that will run
    get_goal_position_thread = threading.Thread(target = update_joy_displacement,args=(my_joy,e2))
    set_goal_position_thread = threading.Thread(target = move_reflex_to_goal_positions, args=(palm,e2))


    get_goal_position_thread.start()
    set_goal_position_thread.start()



    # The main loop that examines for other UI actions including Joy button/HatLoop until the user clicks the close button.
    done = False

    while done is False:
        screen.fill(WHITE)
        textPrint.reset()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                stop_joy_loop()
                stop_reflex_loop()
            elif event.type == pygame.KEYDOWN:
                key_pressed = event.key
                my_logger.info("Key Ascii Value {} Pressed".format(key_pressed))
            elif event.type == pygame.KEYUP:
                key_released = event.key
                my_logger.info("Key Ascii Value {} Released".format(key_released))
            elif event.type == pygame.JOYBUTTONDOWN:
                button = my_joy.get_button_pressed(event)
                my_logger.info("Button {} pressed".format(button))
                if button == 1:
                    e2.clear()
                    time.sleep(1)
                    palm.move_to_rest_position()
                    gp_servo = palm.read_palm_servo_positions()
                    my_logger.info("Finger Rest Positions {}".format(gp_servo))
                    time.sleep(1)
                    my_logger.info("Setting Event Flag")
                    e2.set()
                else:
                    my_controller.set_button_press(button)

            elif event.type == pygame.JOYBUTTONUP:
                button = my_joy.get_button_released(event)
                my_logger.info("Button {} Released".format(button))
                my_controller.set_button_release(button)
            elif event.type == pygame.JOYHATMOTION:
                my_logger.info("Hat movement - {}".format(my_joy.get_hat_movement(event)))
                pass
            elif event.type == pygame.JOYAXISMOTION:
                pass
            else:
                pass # ignoring other non-logitech joystick event types



        # The code below is to test the measurement of Axes displacement in the Joystick and should be removed
        '''
        Num_Axes = my_joy.axes
        for k in range(0,Num_Axes,1):
            d = my_joy.get_axis_displacement_and_grip(k)
            #my_logger.info("Axis No.: {} Move: {} Displacement: {} Grip: {}".format(k,d[0],d[1],d[2]))
            if d[0] == 1:
                palm.grip_fingers(d[1],d[2])
            elif d[0] == 2:
                palm.space_finger1_and_finger2(d[1],d[2])
        '''
        # end of test code for the measurement of Axes displacement in the Joystick

        textPrint.Screenprint(screen, "When ready to Quit, close the screen")
        textPrint.Yspace()

        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT
        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 20 frames per second OR 50 ms scan rate - 1000/20 = 50 ms Both display and checking of Joystick;
        clock.tick(SCAN_RATE)
