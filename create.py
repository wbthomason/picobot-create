import serial
import time
from sys import argv
import logging

class Create(object):

    """A class to manage the connection to and commands for a Create robot."""
   
    # Opcodes
    START       = (128).to_bytes(1, byteorder='big')
    SAFE_MODE   = (131).to_bytes(1, byteorder='big')
    DRIVE       = (137).to_bytes(1, byteorder='big')
    SENSORS     = (142).to_bytes(1, byteorder='big')
    QUERY_LIST  = (149).to_bytes(1, byteorder='big')
    STREAM      = (148).to_bytes(1, byteorder='big')
    LED         = (139).to_bytes(1, byteorder='big')

    # Direction encodings
    NORTH   = 0
    SOUTH   = 1
    EAST    = 2
    WEST    = 3

    # Speeds
    SLOW_FORWARD    = (200).to_bytes(2, byteorder='big', signed=True)
    SLOW_BACKWARD   = (-200).to_bytes(2, byteorder='big', signed=True)
    FAST_FORWARD    = (500).to_bytes(2, byteorder='big', signed=True)
    FAST_BACKWARD   = (-500).to_bytes(2, byteorder='big', signed=True)
    STATIONARY      = (0).to_bytes(2, byteorder='big')

    # Rotations
    STRAIGHT    = bytes.fromhex('8000')
    CLOCKWISE   = bytes.fromhex('ffff')
    COUNTER     = bytes.fromhex('0001')

    def __init__(self, port_name):
        self.connection = serial.Serial()
        self.connection.baudrate = 57600
        self.connection.port = port_name
        self.direction = Create.NORTH
        logging.basicConfig(format='[%(levelname)s] %(asctime)s :>> %(message)s')
        self.log = logging.getLogger('Create-{}'.format(port_name))
        self.log.setLevel(logging.INFO)

    
    def __enter__(self):
        self.log.info('Opening connection to Create on {}'.format(self.connection.port))
        self.connection.open()
        self.log.info('Sending START opcode')
        self.connection.write(Create.START)
        self.log.info('Sending SAFE_MODE opcode')
        self.connection.write(Create.SAFE_MODE)


    def __exit__(self, type, value, traceback):
        self.log.info('Closing connection to Create on {}'.format(self.connection.port))
        self.connection.close()


    def send(self, command_bytes):
        self.connection.write(command_bytes)

    
    def drive(self, direction):
        if self.direction != direction:
            self.face_direction(direction)
        self.send(Create.DRIVE + Create.SLOW_FORWARD + Create.STRAIGHT)
        time.sleep(3.0)
        self.send(Create.DRIVE + Create.STATIONARY + Create.STRAIGHT)


    
    def face_direction(self, direction):
        pass

    
    def check_direction(self, direction):
        pass


    def blink(self):
        play_advance_on = int('00001010', 2).to_bytes(1, byteorder='big')
        play_advance_off = (0).to_bytes(1, byteorder='big')
        power_color_orange = (127).to_bytes(1, byteorder='big')
        power_color_green = (0).to_bytes(1, byteorder='big')
        power_intensity_full = (255).to_bytes(1, byteorder='big')
        time.sleep(2.0)
        self.log.info('Blinking on...')
        self.connection.write(Create.LED + play_advance_on + power_color_orange +
                power_intensity_full)
        time.sleep(1.0)
        self.log.info('Blinking off...')
        self.connection.write(Create.LED + play_advance_off + power_color_orange +
                power_intensity_full)
        time.sleep(1.0)
        self.log.info('Blinking on...')
        self.connection.write(Create.LED + play_advance_on + power_color_orange +
                power_intensity_full)
        time.sleep(1.0)
        self.log.info('Blinking off...')
        self.connection.write(Create.LED + play_advance_off + power_color_orange +
                power_intensity_full)
        time.sleep(1.0)
        self.log.info('Blinking on...')
        self.connection.write(Create.LED + play_advance_on + power_color_orange +
                power_intensity_full)
        time.sleep(1.0)
        self.log.info('Blinking off...')
        time.sleep(1.0)
        self.connection.write(Create.LED + play_advance_off + power_color_orange +
                power_intensity_full)
        self.log.info('Blinking on...')
        self.connection.write(Create.LED + play_advance_on + power_color_orange +
                power_intensity_full)
        time.sleep(1.0)
        self.log.info('Blinking off...')
        self.connection.write(Create.LED + play_advance_off + power_color_orange +
                power_intensity_full)
        self.log.info('Resetting Power LED color')
        self.connection.write(Create.LED + play_advance_off + power_color_green
                + power_intensity_full)

if __name__ == '__main__':
    create = Create(argv[1])
    with create:
        create.blink()
        create.drive(Create.NORTH)
