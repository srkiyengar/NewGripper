__author__ = 'srkiyengar'

import random
from datetime import datetime


SOME_MIN_RANDOM_NUMBER = 1000
SOME_MAX_RANDOM_NUMBER = 1999

rand = some_random_number = random.randrange(SOME_MIN_RANDOM_NUMBER,SOME_MAX_RANDOM_NUMBER)
file_prefix = str(datetime.now())[:16]


class displacement_file():
    def __init__(self):
        global rand
        self.filename = "Servo-displacement-"+file_prefix+"-"+str(rand)
        rand +=1
        try:
            self.fp = open(self.filename,"w")
        except IOError:
            raise IOError ("Unable to open file for recording Servo time")

    def write_data(self, new_str):
        self.fp.write(new_str)
        self.fp.flush()

    def close_file(self):
        self.fp.close()
