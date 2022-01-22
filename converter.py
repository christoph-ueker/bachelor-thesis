"""
This module converts the export text file from a UPPAAL simulation to
the used log format in the main module.
"""

import math
import os
import sys
import re


class Event:
    """Class for events read from logs

    Attributes:
        signal: either Req or Ack
        origin: either 0 for SUT or the number of a Env Node
        target: either 0 for SUT or the number of a Env Node
        ts:     timestamp
        type:   either SUT or ENV, depending on origin
    """
    def __init__(self, signal, origin, target, ts):
        self.signal = signal
        self.origin = origin
        self.target = target
        self.ts = ts

        if self.origin in [0, '-']:
            self.type = "SUT"
        else:
            self.type = "Env"

    # debug printing
    def __str__(self):
        return "signal={0}, origin={1}, target={2}, timestamp={3}".format(str(self.signal), str(self.origin),
                                                                          str(self.target), str(self.ts))


class Log:
    """Contains list of events

    Attributes:
        events: list of events from class Event
    """
    def __init__(self):
        self.events = []

    # debug printing
    def __str__(self):
        ret = ""
        for event in self.events:
            ret += str(event) + "\n"
        return ret


# we receive the following parameters from the simulator
node_count = int(sys.argv[1])
sim_count = int(sys.argv[2])
in_path = sys.argv[3]
print("Converter is running now...")
# print("Reading from path: " + in_path)


def mapping(number):
    """This is the chosen mapping between the values for the integers and their corresponding signal.

    :param int number:  number defined in the adjusted UPPAAL paper_system called simulator.xml
    :return:            signal used for learning process
    :rtype:             str
    """
    signal = ""
    # 8 types of signals
    # if number == -1:
    #     return "Req10"
    if number % 7 == 0:
        return "Req" + str(math.floor(number / 7) + 1) + "x0"
    if number % 7 == 1:
        return "Ack" + "0x" + str(math.floor(number / 7) + 1)
    if number % 7 in [2, 6]:
        return "Req" + "0x" + str(math.floor(number / 7) + 1)
    if number % 7 == 3:
        return "Ack" + str(math.floor(number / 7) + 1) + "x0"
    if number % 7 == 4:
        return "To" + str(math.floor(number / 7) + 1)
    if number % 7 == 5:
        return "To" + str(math.floor(number / 7) + 1)
    return signal


def del_duplicates(arr):
    """Deletes every second line, as they are duplicates from UPPAAL simulation

    :param list of Log arr: log list
    :return:                adjusted log list
    :rtype:                 list of Log
    """
    temp = []
    for i in range(len(arr)):
        if arr[i][1] != arr[i - 1][1]:
            temp.append(arr[i])
    return temp


with open(in_path, 'r') as trace_file:
    lines = trace_file.readlines()

    # save lines to array
    lines = [line.rstrip() for line in lines]

    # drop first lines containing irrelevant information
    for i in range(len(lines)):
        if lines[i][0] == "c":
            drop_first_n = i
            break
    del lines[:drop_first_n]
trace_file.close()
# print(lines)

logs = [[]]
i = -1

for line in lines:
    if line[0] == "c":
        logs.append([])
        i += 1
    else:
        x, y = line.split(': ')
        logs[i].append(y)
# del logs[-1]


# for log in logs:
#     print("--- log ---")
#     for event in log:
#         print(event)

# rearrange to logs
arranged_logs = []
for i in range(sim_count):
    arranged_logs.append([])

pattern = '\(\d+.\d+,\d+\)|\(\d+,\d+\)'
for j in range(node_count):
    # Drop the first simulation, as it does weird stuff anyways
    # @see input of simulations
    for i in range(1, sim_count):
        data = re.findall(pattern, logs[j][i])
        # drop the first tuple due to weird UPPAAL logging
        del data[0]
        # print("XXX")
        # print(' '.join(data))
        arranged_logs[i].append(' '.join(data))

sim_count -= 1
del arranged_logs[0]

# for log in arranged_logs:
#     print("---")
#     print(log)

logs = [[]]
for i in range(sim_count):
    logs.append([])

# print(" ")

# round values to int
for index, log in enumerate(arranged_logs):
    for events in log:
        # print(events)
        data = re.findall(pattern, events)
        for item in data:
            x, y = item[1:-1].split(',')
            logs[index].append((round(float(x)), int(y)))

# for log in logs:
#     print("--- log ---")
#     for event in log:
#         print(event)

# print results to separate text file for further workings
output = open("traces_output.txt", 'w')

log_number = 0
# delete duplicates
for index, log in enumerate(logs):
    # drop the first one to do weird simulations by UPPAAL
    if index > 0:
        # log = list(dict.fromkeys(log))
        log = del_duplicates(log)

        # sort by time (first part of tuple)
        log = sorted(log, key=lambda x: x[0])

        log_number += 1
        output.write("log: " + str(log_number) + "\n")
        for i, event in enumerate(log):

            event_string = "<"
            event_string += mapping(event[1]) + "," + str(event[0]) + ">"
            output.write(str(event_string) + "\n")
output.close()
