import serial
import time
from sys import argv
import logging


direction_map = {'N': 0, 'E': 2, 'W': 3, 'S': 1}


class Create(object):

    """A class to manage the connection to and commands for a Create robot."""
   
    # Opcodes
    START           = (128).to_bytes(1, byteorder='big')
    FULL_MODE       = (132).to_bytes(1, byteorder='big')
    DRIVE           = (137).to_bytes(1, byteorder='big')
    READ_BUMPER     = (142).to_bytes(1, byteorder='big') + (7).to_bytes(1, byteorder='big')
    LED             = (139).to_bytes(1, byteorder='big')
    WAIT_DIST       = (156).to_bytes(1, byteorder='big')
    WAIT_ANGLE      = (157).to_bytes(1, byteorder='big')


    # Direction encodings
    NORTH   = 0
    SOUTH   = 1
    EAST    = 2
    WEST    = 3

    direction_names = ['North', 'South', 'East', 'West']

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

    # Distances
    STRIDE = (100).to_bytes(2, byteorder='big', signed=True)
    BUMP = (50).to_bytes(2, byteorder='big', signed=True)
    UNBUMP = (-50).to_bytes(2, byteorder='big', signed=True)

    # Angles
    RIGHT_ANGLE_CLOCKWISE   = (-90).to_bytes(2, byteorder='big', signed=True)
    RIGHT_ANGLE_COUNTER     = (90).to_bytes(2, byteorder='big', signed=True)
    ONE80_CLOCKWISE         = (-180).to_bytes(2, byteorder='big', signed=True)
    ONE80_COUNTER           = (180).to_bytes(2, byteorder='big', signed=True)
    NO_TURN                 = (0).to_bytes(2, byteorder='big', signed=True)


    # Turning map
    turn_map = [
            [
                (STRAIGHT, NO_TURN),
                (CLOCKWISE, ONE80_CLOCKWISE),
                (CLOCKWISE, RIGHT_ANGLE_CLOCKWISE),
                (COUNTER, RIGHT_ANGLE_COUNTER)
            ],
            [
                (COUNTER, ONE80_COUNTER),
                (STRAIGHT, NO_TURN),
                (COUNTER, RIGHT_ANGLE_COUNTER),
                (CLOCKWISE, RIGHT_ANGLE_CLOCKWISE)
            ],
            [
                (COUNTER, RIGHT_ANGLE_COUNTER),
                (CLOCKWISE, RIGHT_ANGLE_CLOCKWISE),
                (STRAIGHT, NO_TURN),
                (CLOCKWISE, ONE80_CLOCKWISE)
            ],
            [
                (CLOCKWISE, RIGHT_ANGLE_CLOCKWISE),
                (COUNTER, RIGHT_ANGLE_COUNTER),
                (COUNTER, ONE80_COUNTER),
                (STRAIGHT, NO_TURN)
            ]
        ]

    def __init__(self, port_name):
        self.connection = serial.Serial()
        self.connection.baudrate = 57600
        self.connection.port = port_name
        self.orientation = Create.NORTH
        logging.basicConfig(format='%(name)s: [%(levelname)s] %(asctime)s >> %(message)s')
        self.log = logging.getLogger('Create on {}'.format(port_name))
        self.log.setLevel(logging.INFO)

    
    def __enter__(self):
        self.log.info('Opening connection to Create')
        self.connection.open()
        self.log.info('Sending START opcode')
        self.send(Create.START)
        self.log.info('Sending FULL_MODE opcode')
        self.send(Create.FULL_MODE)


    def __exit__(self, type, value, traceback):
        self.log.info('Closing connection to Create')
        self.connection.close()


    def send(self, command_bytes):
        self.connection.write(command_bytes)
        time.sleep(1.0)

    
    def drive(self, direction):
        if self.orientation != direction:
            self.face_direction(direction)

        self.log.info('Driving {}'.format(Create.direction_names[direction]))
        drive_command = Create.DRIVE + Create.SLOW_FORWARD + Create.STRAIGHT 
        wait_command = Create.WAIT_DIST + Create.STRIDE
        stop_command = Create.DRIVE + Create.STATIONARY + Create.STRAIGHT
        self.send(drive_command + wait_command + stop_command)

    
    def face_direction(self, direction):
        self.log.info('Turning to face {}'.format(Create.direction_names[direction]))
        turn_direction, turn_angle = Create.turn_map[self.orientation][direction]
        turn_command = Create.DRIVE + Create.SLOW_FORWARD + turn_direction 
        wait_command = Create.WAIT_ANGLE + turn_angle
        stop_command = Create.DRIVE + Create.STATIONARY + Create.STRAIGHT
        self.send(turn_command + wait_command + stop_command)
        self.orientation = direction

    
    def check_direction(self, direction):
        if self.orientation != direction:
            self.face_direction(direction)

        self.log.info('Checking {}'.format(Create.direction_names[direction]))
        self.send(Create.DRIVE + Create.SLOW_FORWARD + Create.STRAIGHT)
        self.send(Create.WAIT_DIST + Create.BUMP)
        self.send(Create.READ_BUMPER)
        self.send(Create.DRIVE + Create.SLOW_BACKWARD + Create.STRAIGHT)
        self.send(Create.WAIT_DIST + Create.UNBUMP)
        bumper_data = self.connection.read()[0]
        left_bumper = (bumper_data & 0x02) > 0
        right_bumper = (bumper_data & 0x01) > 0
        return left_bumper or right_bumper


    def blink(self):
        play_advance_on = int('00001010', 2).to_bytes(1, byteorder='big')
        play_advance_off = (0).to_bytes(1, byteorder='big')
        power_color_orange = (127).to_bytes(1, byteorder='big')
        power_color_green = (0).to_bytes(1, byteorder='big')
        power_intensity_full = (255).to_bytes(1, byteorder='big')
        self.log.info('Blinking on...')
        self.send(Create.LED + play_advance_on + power_color_orange + power_intensity_full)
        self.log.info('Blinking off...')
        self.send(Create.LED + play_advance_off + power_color_orange + power_intensity_full)
        self.log.info('Blinking on...')
        self.send(Create.LED + play_advance_on + power_color_orange + power_intensity_full)
        self.log.info('Blinking off...')
        self.send(Create.LED + play_advance_off + power_color_orange + power_intensity_full)
        self.log.info('Blinking on...')
        self.send(Create.LED + play_advance_on + power_color_orange + power_intensity_full)
        self.log.info('Blinking off...')
        self.send(Create.LED + play_advance_off + power_color_orange + power_intensity_full)
        self.log.info('Blinking on...')
        self.send(Create.LED + play_advance_on + power_color_orange + power_intensity_full)
        self.log.info('Blinking off...')
        self.send(Create.LED + play_advance_off + power_color_orange + power_intensity_full)
        self.log.info('Resetting Power LED color')
        self.send(Create.LED + play_advance_off + power_color_green + power_intensity_full)

if __name__ == '__main__':
    create = Create(argv[1])
    with create:
        create.blink()
        create.drive(Create.EAST)
        create.drive(Create.WEST)
        print(create.check_direction(Create.WEST))
        print(create.check_direction(Create.SOUTH))
