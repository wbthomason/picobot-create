from sys import argv, exit, stdin
import create
import re
from itertools import groupby
import logging

def collect_state_data():
    '''Reads a Picobot program from stdin'''
    print("Enter your program's states, one line at a time. End with 'q'")
    state_data = []
    for state in stdin:
        state = state.strip()
        if state == 'q':
            return state_data
        state_data.append(state)


def parse(state_data):
    '''Given a set of strings each representing a state, remove comments and
    parse out the relevant parts of each state into a dictionary, grouped by
    state number'''
    state_regex =\
        re.compile(r'(?P<state_num>[0-9]+)\s+(?P<sensor_state>[xXnNsSwWeE*]{4})\s+->\s+(?P<direction>[nNsSwWeE])\s+(?P<new_state>[0-9]+)')
    comment_regex = re.compile(r'.*#.*$')
    state_data = [state_regex.match(state) for state in state_data if not comment_regex.match(state)]
    state_data = [match.groupdict() for match in state_data if match]
    def get_state_num(match_dict):
        return match_dict['state_num']

    return {key: list(group) for key, group in groupby(state_data, get_state_num)}


def load_states(state_filename):
    '''Read a state file if one was provided, else prompt for a set of states on
    stdin. Return the parsed state data.'''
    if state_filename:
        with open(state_filename, 'r') as state_file:
            state_data = state_file.readlines()
    else:
        state_data = collect_state_data()

    return parse(state_data)


direction_map = {'N': 0, 'E': 1, 'W': 2, 'S': 3}


def make_state_machine(states):
    '''Given parsed state data, form a state machine mapping states to pairs of
    directions to check and possible sensor states. Each sensor state maps a
    4-tuple to a direction in which to drive and a new state to which to transition.'''
    machine = {}
    for state in states:
        state_edges = states[state]
        direction_sets = [edge['sensor_state'].upper() for edge in state_edges]
        directions = []
        for dir_state in direction_sets:
            if dir_state[0] != '*':
                directions.append('N')
            if dir_state[1] != '*':
                directions.append('E')
            if dir_state[2] != '*':
                directions.append('W')
            if dir_state[3] != '*':
                directions.append('S')
        directions = set(directions)
        directions = [(direction, create.direction_map[direction]) for direction in\
                directions]
        sensor_states = {edge['sensor_state'].upper():\
                (edge['direction'].upper(), edge['new_state']) for edge in state_edges}

        machine[state] = (directions, sensor_states, direction_sets)

    return machine


def transition(sensor_state, ordered_states):
    '''Check a sensor state against the transition states of a state, to deal
    with translating *s'''
    for state in ordered_states:
        match_flag = True
        for direction in range(4):
            match_flag = match_flag and\
                    (state[direction] == sensor_state[direction] or\
                            state[direction] =='*')
        if match_flag:
            return state

    return 'No such state'


def run_state_machine(machine, create, log):
    '''Execute the state machine by transitioning between states until a
    terminal state is reached'''
    state = '0'
    while True:
        directions, transition_states, ordered_states = machine[state]
        direction_states = [(direction[0], create.check_direction(direction[1])) for direction in directions]
        sensor_state = list('****')
        for dir_name, dir_val in direction_states:
            sensor_state[direction_map[dir_name]] = dir_name if dir_val else 'X'
        sensor_state = ''.join(sensor_state)
        log.info('Read sensor values: {}'.format(sensor_state))
        direction, new_state = transition_states[transition(sensor_state, ordered_states)]
        if direction == 'X':
            return
        log.info('Driving {}'.format(direction))
        create.drive(direction_map[direction])
        log.info('Transitioning to state {}'.format(new_state))
        state = new_state


if __name__ == '__main__':
    logging.basicConfig(format='%(name)s: [%(levelname)s] %(asctime)s >> %(message)s')
    log = logging.getLogger('picobot')
    log.setLevel(logging.INFO)
    log.info('Constructing state machine')
    states = load_states(argv[2] if len(argv) > 2 else None)
    state_machine = make_state_machine(states)
    if not argv[1]:
        print('Give the name of the Bluetooth device as the first positional argument')
        exit(42)

    create = create.Create(argv[1])
    log.info('Starting execution')
    with create:
        run_state_machine(state_machine, create, log)
    log.info('Terminal state reached')
