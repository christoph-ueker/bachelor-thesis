"""
This module converts the export text file from a UPPAAL simulation to
the used log format in the main module.
Performant for at least 10000 logs.
"""

import math
import os


class Event:
    def __init__(self, signal, origin, target, ts):
        # either Req or Ack
        self.signal = signal
        # either 0 for SUT or the number of a Env Node
        self.origin = origin
        # either 0 for SUT or the number of a Env Node
        self.target = target
        # timestamp
        self.ts = ts

        if self.origin in [0, '-']:
            self.type = "SUT"
        else:
            self.type = "Env"

    # required for debugging printing
    def __str__(self):
        return "signal={0}, origin={1}, target={2}, timestamp={3}".format(str(self.signal), str(self.origin),
                                                                          str(self.target), str(self.ts))


# contains list of Event
class Log:
    def __init__(self):
        self.events = []

    # required for debugging printing
    def __str__(self):
        ret = ""
        for event in self.events:
            ret += str(event) + "\n"
        return ret


def mapping(number):
    """
    This is the chosen mapping between the values for the integers and their corresponding
    signal.
    :param number: the number defined in the adjusted UPPAAL paper_system
    :return: signal: Signal used for learning process
    """
    signal = ""
    # 8 types of signals
    if number % 8 == 0:
        signal = "Req" + str(math.floor(number / 8) + 1) + "0"
    if number % 8 == 1:
        signal = "Ack" + "0" + str(math.floor(number / 8) + 1)
    if number % 8 in [2, 6, 7]:
        signal = "Req" + "0" + str(math.floor(number / 8) + 1)
    if number % 8 == 3:
        signal = "Ack" + str(math.floor(number / 8) + 1) + "0"
    if number % 8 == 4:
        signal = "."
        # signal = "TO" + str(math.floor(number / 8) + 1) + "0"
    if number % 8 == 5:
        signal = "."
        # signal = "TO" + str(math.floor(number / 8) + 1) + "00"
    return signal


# deletes every second line, as they are duplicates from UPPAAL
def del_duplicates(arr):
    temp = []
    for i, sth in enumerate(arr):
        if arr[i][1] != arr[i - 1][1]:
            temp.append(arr[i])
    return temp


def wanna_delete_double_to_log(log):
    for i, event in enumerate(log):
        if mapping(log[i][1]) == "." == mapping(log[i - 1][1]):
            return True
    return False


# number of simulations
node_count = 3
sim_count = 0
with open("traces.txt", 'r') as trace_file:
    lines = trace_file.readlines()

    # save lines to array
    lines = [line.rstrip() for line in lines]

    # read number of simulations from first line
    temp = lines[0]
    sim_count = int(temp[temp.rfind("(") + 1:temp.rfind(")"):])
    del lines[0]
trace_file.close()
logs = [[]]
i = -1

for line in lines:
    if line[0] == "#":
        logs.append([])
        i += 1
    logs[i].append(line)
del logs[-1]

# rearrange to logs
arranged_logs = [[]]
for i in range(sim_count - 1):
    arranged_logs.append([])
for i in range(sim_count):
    for j in range(node_count):
        arranged_logs[i] += logs[i + j * sim_count]

logs = [[]]
for i in range(sim_count - 1):
    logs.append([])

# round values to int
for index, log in enumerate(arranged_logs):
    for event in log:
        # only keep useful lines, 100 is the upper time boarder of the used query
        if event[0] not in ["0", "#"] and event[:3] != "100":
            x, y = event.split(' ')
            if y != "-1.0":
                logs[index].append((round(float(x)), int(float(y))))

# print results to separate text file for further workings
output = open("traces_output.txt", 'w')

log_number = 0
# delete duplicates
for log in logs:
    log = del_duplicates(log)
    log = list(dict.fromkeys(log))
    # sort by time (first part of tuple)
    log = sorted(log, key=lambda x: x[0])
    # deleting all logs with two timeouts in a row
    if not wanna_delete_double_to_log(log):
        log_number += 1
        output.write("log: " + str(log_number + 1) + "\n")
        for i, event in enumerate(log):
            event_string = "<"
            event_string += mapping(event[1]) + "," + str(event[0]) + ">"
            output.write(str(event_string) + "\n")
output.close()

# Post output validations
output = open("traces_output.txt", 'r')
logs = []
lines = [line.replace('\n', '').replace('<', '').replace('>', '') for line in output.readlines()]

# TODO: This value is currently given
nodes = 3

for index, line in enumerate(lines):
    # line initializing new event feed for a log (log: x)
    if line[0] == "l":
        if index > 0 and skip_flag == False:
            logs.append(temp)
        temp = Log()
        skip_flag = False
        reqX0_present = []
        for i in range(nodes):
            reqX0_present.append(False)
    else:
        wholesignal, ts = line.split(',')
        ts = int(ts)
        # timeout represented by wildcard '.'
        if wholesignal != '.':
            # first 3 characters are Req or Ack
            signal = wholesignal[:3]
            origin = int(wholesignal[3])
            target = int(wholesignal[4])
            for i in range(nodes):
                if signal == "Req" and origin-1 == i:
                    reqX0_present[i] = True
                elif (signal != "Req") and (target-1 == i or origin-1 == i) and (reqX0_present[i] == False):
                    skip_flag = True
        else:
            signal = "."
            origin = ""
            target = ""
        temp.events.append(Event(signal, origin, target, ts))

output.close()
os.remove("traces_output.txt")
output = open("traces_output.txt", 'w')
log_number = 0
for log in logs:
    log_number += 1
    output.write("log: " + str(log_number) + "\n")
    for i, event in enumerate(log.events):
        event_string = "<"
        event_string += event.signal + str(event.origin) + str(event.target) + "," + str(event.ts) + ">"
        output.write(str(event_string) + "\n")
output.close()
