__author__ = 'srkiyengar'

import random
from datetime import datetime
import logging


# This logger is setup in the main python script
my_logger = logging.getLogger("My_Logger")
LOG_LEVEL = logging.DEBUG


class displacement_file():
    def __init__(self, rand):
        file_prefix = str(datetime.now())[:16]
        self.prefix = file_prefix
        self.filename = "Servo-displacement-"+file_prefix+"-"+str(rand)
        try:
            self.fp = open(self.filename,"w")
            my_logger.info('file {} created'.format(self.filename))
        except IOError:
            raise IOError ("Unable to open file for creating datafile")


    def get_file_prefix(self):
        return self.prefix

    def write_data(self, new_str):
        self.fp.write(new_str)
        self.fp.flush()

    def close_file(self):
        self.fp.close()


class servo_position_file():
    def __init__(self,the_rand, the_prefix):
        self.filename = "Servo-position-"+the_prefix+"-"+str(the_rand)
        try:
            self.fp1 = open(self.filename,"w")
            my_logger.info('file {} created'.format(self.filename))
        except IOError:
            raise IOError ("Unable to open file for creating servo position file")

    def write_data(self, this_str):
        self.fp1.write(this_str)
        self.fp1.flush()

    def close_file(self):
        self.fp1.close()