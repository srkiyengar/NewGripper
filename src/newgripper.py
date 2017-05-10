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
import data_collect as dc
import random
import tcp_client as tc


SOME_MIN_RANDOM_NUMBER = 1000
SOME_MAX_RANDOM_NUMBER = 1999

'''
The default model for Joystick displacement for moving servo is 1. Here a non-zero joystick displacement will
create a new goal position for the reflex at the sampling rate (reflex_loop_rate) as long as the program is running.
Other option being considered is value 0 where the joystick displacement is mapped to a position in the span of the
finger movement. The lower position (start position) is set by calibration and the upper position is set by the
MAX_FINGER_MOVEMENT which is set to an approximate valuse corresponding the to span. The fingers are restricted to
moving within this limit.

'''
METHOD = 1

POS_ERROR = 20

#logger
LOG_LEVEL = logging.DEBUG
LOG_FILENAME = 'NewGripper' + datetime.now().strftime('%Y-%m-%d---%H:%M:%S')

# Define some colors
BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)

SCAN_RATE = 20                    #1 (one) second divided by scan rate is the loop checking if the main program should stop


joy_y_position = 0.0
joy_x_position = 0.0


# Setting the maximum cycle rate for the two threads 1)joystick loop and 2) servo command to move gripper
joy_loop_rate = 1000    # in microsecond
reflex_loop_rate = 16000    # in microsecond
servo_loop_rate = 500000      # in microsecod



last_time = datetime.now()
my_lock = threading.Lock()      # shared variables between joy and reflex thread are accessed through a lock

all_loop = True                 # loop control for threads

joy_measurement_ts = 0.0        # joystick displacement measurement timestamp
joy_moved = False               # This is to restrict logging to logger only when there is a change in displacement



record_displacement = False     # When to record finger position with time for gripping



def stop_all_thread():
    '''
    This will set the control to false and the threads will stop
    :return:
    '''
    global all_loop
    time.sleep(1)
    all_loop = False



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
    global joy_moved, joy_y_position, joy_x_position, joy_measurement_ts
    while all_loop:
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

        #if ("go in"):
        if axis_x != 0 or axis_y != 0:
            my_logger.info('Joystick Thread Counter: {} Time: {} Aperture Disp. {} Preshape Disp. {}'.
                            format(counter, str(measurement_time)[17:],axis_y,axis_x))

            with my_lock:
                joy_moved = True        # This is a flag to indicate Joystick is displaced from rest position.
                joy_measurement_ts = measurement_time
                joy_y_position = axis_y
                joy_x_position = axis_x

            my_logger.info('Joy displacement flag is {} '.format(joy_moved))
            counter += 1

            last_joy_time = present_time


def move_reflex_to_goal_positions(my_joy,palm,e2):
    '''
    This is to move the Reflex to joy_disp position at the rate set by
    'reflex_loop_rate'
    :type e2: event object
    :param my_joy: Joystick object
    :param palm: This is the reflex object in the main e2: event communication between main and the threads especially
    for calibrating the joystick.
    :return:
    '''
    counter = 1
    global last_time, joy_moved
    last_reflex_time = last_time

    previous_command_time = 0
    while all_loop:
        e2.wait()       # This is used to pause the thread in case we want to calibrate the gripper
        present_time = datetime.now()
        delta_t = present_time - last_reflex_time
        delta_t = delta_t.seconds*1000000 + delta_t.microseconds

        if (delta_t < reflex_loop_rate):
            delay = reflex_loop_rate - delta_t
            delay_in_seconds = delay/1000000.0
            time.sleep(delay_in_seconds)
            #what_time = datetime.now()
            #delta_t =   what_time - last_reflex_time
            #delta_t = delta_t.seconds*1000000 + delta_t.microseconds

        with my_lock:
            y_displacement = joy_y_position
            x_displacement = joy_x_position
            move_servo = joy_moved
            joy_ts = joy_measurement_ts
            collect_data = record_displacement

        command_time = datetime.now()

        if move_servo and reflex.servo_move_with_joy:
            my_logger.info('Thread Reflex Counter: {} - Time: {} Aperture (Y) disp {} Pre-shape (X) disp'.
                           format(counter, command_time, y_displacement,x_displacement))
            # Sending the displacement to move_fingers in reflex.py to process
            with my_lock:
                #servo_gp will be 4 numbers in a list corresponding to servo 1,2,3,4
                servo_gp = palm.move_fingers(my_joy,y_displacement,x_displacement)
                if collect_data:
                    time_before_position_command = datetime.now()
                    v = palm.servo_current_position_if_not_moving_all()
                    time_after_position_command = datetime.now()
                    time_elapsed = time_after_position_command-time_before_position_command
                    time_elapsed = time_elapsed.seconds*1000000+time_elapsed.microseconds
                    '''
                    c_diff = command_time - previous_command_time
                    c_diff_micro= c_diff.seconds*1000000+c_diff.microseconds
                    my_data_file.write_data(str(counter)+"->"+str(delta_t)+'--#,'+str(command_time)+","+str(previous_command_time)+","+
                                            str(c_diff.seconds)+","+str(c_diff.microseconds)+'\n')
                    '''
                    my_data_file.write_data(str(joy_ts)+","+str(y_displacement)+","+
                                                    str(x_displacement)+","+str(command_time)+","+
                                                    str(servo_gp).strip("[]")+",**" +
                                                    str(time_before_position_command) + ","+str(time_elapsed)+
                                                    "," + str(v).strip("[]")+'\n')
                joy_moved = False
                my_logger.info('Reflex Thread - Resetting Joy Displacement Flag to {}'.format(joy_moved))

        counter += 1
        previous_command_time = command_time
        last_reflex_time = present_time
    my_logger.info('Exit Reflex thread')

def record_servo_position(palm,e2):

    '''
    This will independantly record the servo position; The idea is to identify the time at which aperture = minimum.
    sufficient to grip an object. It should alos provide the aperture position
    :param palm:
    :param e2:
    :return:
    '''
    counter = 1
    global last_time
    last_loop_time = last_time
    # previous_command_time = last_time
    while all_loop:
        e2.wait()       # This is used to pause the thread in case we want to calibrate the gripper
        present_time = datetime.now()
        delta_t = present_time - last_loop_time
        delta_t = delta_t.seconds*1000000 + delta_t.microseconds

        if (delta_t < servo_loop_rate):
            ndelay = servo_loop_rate - delta_t
            ndelay = ndelay/1000000.0
            my_logger.info('Should wait {}'.format(ndelay))
            time.sleep(ndelay)

        with my_lock:
            record_servo = joy_moved
            collect_servo_position = record_displacement

        if record_servo:
            with my_lock:
                command_time = datetime.now()
                v = palm.servo_current_position_if_not_moving(1)
                if collect_servo_position:
                    '''
                    diff = command_time-previous_command_time
                    val = (diff.seconds*1000000 + diff.microseconds)/1000
                    my_servo_file.write_data("Present Time: {} - Last Loop Time: {}\n".
                                             format(present_time,last_loop_time))
                    my_servo_file.write_data("Command time: {} - Previous Command Time: {}\n".
                                             format(command_time,previous_command_time))
                    my_servo_file.write_data(str(command_time)+": "+str(v)+ " Diff: "+str(val)  +"\n")
                    '''
                    #uncomment the line below if file needs to be written to.
                    #my_servo_file.write_data(str(command_time)+": "+str(v)+"\n")
                # previous_command_time = command_time
        counter += 1
        last_loop_time = present_time
    my_logger.info('Exit servo thread')


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

    try:
        joy_logitech = js.ExtremeProJoystick()
    except:
        try:
            joy_thumstick = js.Thumbstick()
        except:
            raise RuntimeError('Joystick not found\n')
        else:
            my_joy = joy_thumstick
    else:
        my_joy = joy_logitech

    my_controller = reflex.joy_reflex_controller(my_joy,palm)
    my_key_controller = reflex.key_reflex_controller(palm)

    # Event to pause the thread
    e2 = threading.Event()
    e2.set()    #Flag is set to allow the thread move_reflex_to_goal_positions to run

    calibrate = False


    key_ring={}
    key_ring['301']= 0  # 301 is Caps lock. This will be displayed in the screen  Caps lock = 1 + keys are the command set
    key_pressed = 0     # key press and release will happen one after another
    key_released = 0

    file_ring={}        # to make sure we close any file created only if it is not closed

    method = METHOD
    # Calibration
    while calibrate is False:
        screen.fill(WHITE)
        textPrint.reset()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                key_pressed = event.key
                my_logger.info("Key Ascii Value {} Pressed".format(key_pressed))
                key_ring[str(key_pressed)] = 1
                if key_ring['301'] == 1:    # Caps lock is 1
                    if my_key_controller.set_key_press(key_pressed) == 1:
                        calibrate = True
            elif event.type == pygame.KEYUP:
                key_released = event.key
                my_logger.info("Key Ascii Value {} Released".format(key_released))
                key_ring[str(key_released)] = 0
            else:
                pass # ignoring other non-logitech joystick event types

        textPrint.Screenprint(screen, "Caps Lock should be 1 to accept any of the keys")
        textPrint.Yspace()
        textPrint.Yspace()
        textPrint.Screenprint(screen,"Caps Lock Key set to {}".format(key_ring['301']))
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Finger 1 - Press 'q' to move up")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Finger 1 - Press 'a' to move down")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Finger 2 - Press 'w' to move up")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Finger 2 - Press 's' to move down")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Finger 3 - Press 'e' to move up")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Finger 3 - Press 'd' to move down")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Pre Shape - Press 'r' to move closer")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Pre Shape - Press 'f' to move away")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Pressing 'l (L)' toggles servo data file capture when No NDI measurement")
        textPrint.Yspace()
        textPrint.Yspace()
        textPrint.Screenprint(screen,"NDI connection is {} (Toggle with n)".format(reflex.ndi_measurement))
        textPrint.Yspace()
        textPrint.Screenprint(screen,"Servo data file collection {}".format(reflex.log_data_to_file))
        textPrint.Yspace()
        textPrint.Screenprint(screen,"Joystick control of gripper method is {}".format(reflex.control_method))
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Is labview program running? if NDI connection is True")
        textPrint.Yspace()
        textPrint.Screenprint(screen, "Press 'c' when calibration is complete")

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 20 frames per second OR 50 ms scan rate - 1000/20 = 50 ms Both display and checking of Joystick;
        clock.tick(SCAN_RATE)

    # Calibration completed




    #setup labview connection
    labview_connection = False
    if(reflex.ndi_measurement):
        my_connector = tc.command_labview('192.168.10.2', 5000)
        if my_connector.connected == 1:
            my_clock_sync = tc.sync_time(my_connector,10)
            my_clock_sync.get_time_diff()
            transit_time = my_clock_sync.transit_time
            #my_dataset.set_transit_time(transit_time)
            if(my_clock_sync.transit_error == 0):
                difference = my_clock_sync.clock_difference
                #my_dataset.set_clock_difference(difference)
            else:
                my_logger.info(
                    "Clock Difference cannot be computed as transit time (micros): {} above 2ms".format(transit_time))
                    # raise RuntimeError('Transit Time in milliseconds too high to sync clock', (transit_time/1000),'\n')
            labview_connection = True       # with labview running, this program has established  tcp connection
            my_logger.info("Labview connection success")
        else:
            labview_connection = False
            my_logger.info("Labview connection failure")



    # preparing the two threads that will run
    get_goal_position_thread = threading.Thread(target = update_joy_displacement,args=(my_joy,e2))
    set_goal_position_thread = threading.Thread(target = move_reflex_to_goal_positions, args=(my_joy,palm,e2))
    #get_servo_position_thread = threading.Thread(target = record_servo_position, args=(palm,e2))

    # Two threads started
    get_goal_position_thread.start()
    set_goal_position_thread.start()
    #get_servo_position_thread.start()



    # The main loop that examines for other UI actions including Joy button/HatLoop until the user clicks the close button.
    done = False
    my_rand = some_random_number = random.randrange(SOME_MIN_RANDOM_NUMBER,SOME_MAX_RANDOM_NUMBER)
    while done is False:
        screen.fill(WHITE)
        textPrint.reset()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                stop_all_thread()
                time.sleep(0.5)
                palm.move_to_lower_limits()
                gp_servo = palm.read_palm_servo_positions()
                my_logger.info("Finger moved back to Lower Limit Positions {}".format(gp_servo[1:]))
            elif event.type == pygame.KEYDOWN:
                key_pressed = event.key
                my_logger.info("Key Ascii Value {} Pressed".format(key_pressed))
                key_ring[str(key_pressed)] = 1
                if key_ring['301'] == 1:    # Caps lock is 1
                    e2.clear()
                    time.sleep(0.5)
                    my_key_controller.set_key_press(key_pressed)
                    time.sleep(0.2)
                    e2.set()
            elif event.type == pygame.KEYUP:
                key_released = event.key
                my_logger.info("Key Ascii Value {} Released".format(key_released))
                key_ring[str(key_released)] = 0
            elif event.type == pygame.JOYBUTTONDOWN:
                button = my_joy.get_button_pressed(event)
                my_logger.info("Button {} pressed".format(button))
                if button == 0:
                    gp_servo = palm.read_palm_servo_positions()
                    my_logger.info("Finger Current Positions {}".format(gp_servo[1:]))
                elif button == 1:
                    task_start_time = datetime.now()
                    if reflex.ndi_measurement or reflex.log_data_to_file:
                        with my_lock:
                            # Close the previous file if it exists
                            if (record_displacement == True):   # only when button was previously pressed
                                if(file_ring[my_data_file.filename]== 1):
                                    my_data_file.close_file()
                                    file_ring[my_data_file.filename]=0
                                    if labview_connection:
                                        my_connector.stop_collecting()
                            else:
                                record_displacement = True
                        my_data_file = dc.displacement_file(my_rand)
                        file_ring[my_data_file.filename]=1
                        my_data_file.write_data("Start time: "+str(task_start_time)+'\n')
                        # Time difference between Labview PC and the Laptop running Gripper

                        my_rand += 1
                        if labview_connection:
                            my_data_file.write_data("Time Difference between Labview PC and the Laptop running Gripper"
                                            "(+ive means Desktop is ahead): "+str(my_clock_sync.clock_difference)+'\n')
                            my_connector.start_collecting(my_data_file.id)
                    '''
                        my_servo_file = dc.servo_position_file(my_rand,my_data_file.get_file_prefix())
                        file_ring[my_servo_file.filename]=1
                    '''
                # Sends the fingers to lower limits for now
                elif button == 3:
                    e2.clear()
                    time.sleep(1)
                    palm.move_to_lower_limits()
                    gp_servo = palm.read_palm_servo_positions()
                    my_logger.info("Finger Lower Limit Positions {}".format(gp_servo[1:]))
                    time.sleep(1)
                    my_logger.info("Setting Event Flag")
                    e2.set()
                #button 5 helps end recoding for good where as 1 get ready for next recording
                elif button == 5:
                    task_end_time = datetime.now()
                    if reflex.ndi_measurement or reflex.log_data_to_file:
                        with my_lock:
                            if (record_displacement == True):   # only when button was previously pressed
                                if(file_ring[my_data_file.filename]== 1):
                                    total_task_time = task_end_time - task_start_time
                                    total_task_time = total_task_time.seconds+ total_task_time.microseconds/1000000.0
                                    my_data_file.write_data("Start time: "+str(task_start_time)+'\n')
                                    my_data_file.write_data("End time: "+str(task_end_time)+'\n')
                                    my_data_file.write_data("Task_time: "+str(total_task_time)+'\n')
                                    my_data_file.write_data(palm.get_move_finger_control_method()+'\n')
                                    my_data_file.close_file()
                                    file_ring[my_data_file.filename]=0
                                    if(reflex.ndi_measurement):
                                        my_connector.stop_collecting()
                                '''
                                if(file_ring[my_servo_file.filename]== 1):
                                    my_servo_file.close_file()
                                    file_ring[my_servo_file.filename]=0
                                '''
                                record_displacement = False

            elif event.type == pygame.JOYBUTTONUP:
                my_logger.info("Button {} Released".format(button))
            elif event.type == pygame.JOYHATMOTION:
                my_logger.info("Hat movement - {}".format(my_joy.get_hat_movement(event)))
                pass
            elif event.type == pygame.JOYAXISMOTION:
                pass
            else:
                pass # ignoring other non-logitech joystick event types

        textPrint.Screenprint(screen, "When ready to Quit, close the screen")
        textPrint.Yspace()
        textPrint.Screenprint(screen,"Caps Lock Key Pressed {}".format(key_ring['301']))
        textPrint.Yspace()
        textPrint.Screenprint(screen," Method of Joy displacement control Of Gripper")
        textPrint.Yspace()
        textPrint.Screenprint(screen,"(by Velocity if 1 or by displacement if 2) =  {}".
                              format(reflex.control_method))
        textPrint.Yspace()
        textPrint.Screenprint(screen,"NDI connection is {}".format(reflex.ndi_measurement))
        textPrint.Yspace()
        textPrint.Screenprint(screen,"Logging servo data file (Toggle with l)---> {} ".format(reflex.log_data_to_file))
        textPrint.Yspace()
        textPrint.Screenprint(screen,"Joystick drives Gripper (Toggle with x) ----> {}".format(reflex.servo_move_with_joy))

        #textPrint.indent()
        #textPrint.Yspace()
        #textPrint.Screenprint(screen, "Num Lock Key Released: {}".format(key_released))
        #textPrint.unindent()

        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT
        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 20 frames per second OR 50 ms scan rate - 1000/20 = 50 ms Both display and checking of Joystick;
        clock.tick(SCAN_RATE)

    if(reflex.ndi_measurement):
        my_connector.destroy()


