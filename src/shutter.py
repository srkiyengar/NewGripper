import serial
import struct
import time

# j = 2 means open, j = 1 means close shutter
def command_shutter(port, j):

    # first, start the serial port to communicate with the arduino
    if port.isOpen():
        print "port open"
        port.write(struct.pack('>B', j))
        return 1
    else:
        return 0
    #while(1 == 1):
        #cover_or_not = int(input('Enter a number. 1 will cover the Lenses of the NDI, while 2 will open the blinds.'))
        #data.write(struct.pack('>B',cover_or_not))