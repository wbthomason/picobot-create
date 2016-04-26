from sys import argv, exit, stdin
import create
import re
from itertools import groupby
import logging

def collect_state_data():
    print("Enter your program's states. End with 'q'")
    state_data = []
    for state in stdin:
        state = state.strip()
        if state == 'q':
            return state_data
        state_data.append(state)


def parse(state_data):
    state_regex =\
        re.compile(r'(?P<state_num>[0-9]+)\s+(?P<sensor_state>[xXnNsSwWeE*]{4})\s+->\s+(?P<direction>[nNsSwWeE])\s+(?P<new_state>[0-9]+)')
    comment_regex = re.compile(r'.*#.*$')
    state_data = [state_regex.match(state) for state in state_data if not comment_regex.match(state)]
    state_data = [match.groupdict() for match in state_data if match]
    def get_state_num(match_dict):
        return match_dict['state_num']

    return {key: list(group) for key, group in groupby(state_data, get_state_num)}


def load_states(state_filename):
    if state_filename:
        with open(state_filename, 'r') as state_file:
            state_data = state_file.readlines()
    else:
        state_data = collect_state_data()

    return parse(state_data)


direction_map = {'N': 0, 'E': 1, 'W': 2, 'S': 3}


def make_state_machine(states):
    machine = {}
    for state in states:
        state_edges = states[state]
        direction_sets = [set(edge['sensor_state'].upper()) for edge in state_edges]
        directions = set()
        for dir_set in direction_sets:
            directions = directions | dir_set

        directions -= set('*')
        directions = [(direction, create.direction_map[direction]) for direction in\
                directions]
        sensor_states = {edge['sensor_state'].upper():\
                (edge['direction'].upper(), edge['new_state']) for edge in state_edges}

        machine[state] = (directions, sensor_states)

    return machine



def run_state_machine(machine, create, log):
    state = '0'
    while True:
        directions, transition_states = machine[state]
        direction_states = [(direction[0], create.check_direction(direction[1])) for direction in directions]
        sensor_state = '****'
        for dir_name, dir_val in direction_states:
            sensor_state[direction_map[dir_name]] = dir_name if dir_val else 'X'
        direction, new_state = transition_states[sensor_state]
        if direction == 'X':
            return
        create.drive(create.direction_map[direction])
        state = new_state


if __name__ == '__main__':
    logging.basicConfig(format='%(name): [%(levelname)s] %(asctime)s >> %(message)s')
    log = logging.getLogger('picobot')
    log.setLevel(logging.INFO)
    states = load_states(argv[2] if len(argv) > 2 else None)
    state_machine = make_state_machine(states)
    if not argv[1]:
        print('Give the name of the Bluetooth device as the first positional argument')
        exit(42)

    create = create.Create(argv[1])
    with create:
        run_state_machine(state_machine, create, log)
