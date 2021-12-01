"""
This module converts the export text file from a UPPAAL simulation to
the used log format in the main module.
"""

import math
import os
from main import Event
from main import Log


"""
Set these
"""
# number of Env nodes
node_count = 3


def mapping(number):
    """This is the chosen mapping between the values for the integers and their corresponding signal.

    :param int number:  number defined in the adjusted UPPAAL paper_system called paper_system_input
    :return:            signal used for learning process
    :rtype:             str
    """
    signal = ""
    # 8 types of signals
    if number == -1:
        return "Req10"
    if number % 8 == 0:
        return "Req" + str(math.floor(number / 8) + 1) + "0"
    if number % 8 == 1:
        return "Ack" + "0" + str(math.floor(number / 8) + 1)
    if number % 8 in [2, 6, 7]:
        return "Req" + "0" + str(math.floor(number / 8) + 1)
    if number % 8 == 3:
        return "Ack" + str(math.floor(number / 8) + 1) + "0"
    if number % 8 == 4:
        return "To" + str(math.floor(number / 8) + 1)
    if number % 8 == 5:
        return "To" + str(math.floor(number / 8) + 1)
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


# TODO: Not used anymore
def wanna_delete_double_to_log(log):
    # print("deleting log")
    for i, event in enumerate(log):
        if mapping(log[i][1]) == "." and mapping(log[i - 1][1]) == ".":
            return True
    return False


sim_count = 0
with open("traces.txt", 'r') as trace_file:
    lines = trace_file.readlines()

    # save lines to array
    lines = [line.rstrip() for line in lines]

    # read number of simulations from first line
    temp = lines[0]
    sim_count = int(temp[temp.rfind("(") + 1:temp.rfind(")"):])
    # drop first line
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
for i in range(sim_count - 1):
    for j in range(node_count):
        arranged_logs[i] += logs[i + j * sim_count]

# for log in arranged_logs:
#     print("--- log ---")
#     for event in log:
#         print(event)

logs = [[]]
for i in range(sim_count - 1):
    logs.append([])

# round values to int
for index, log in enumerate(arranged_logs):
    for id, event in enumerate(log):
        # only keep useful lines
        if event[0] != '#' and log[id - 1][0] != '#':
            x, y = event.split(' ')
            if y != "0.0":
                logs[index].append((round(float(x)), int(float(y))))

# for log in logs:
#     print("--- log ---")
#     for event in log:
#         print(event)

# print results to separate text file for further workings
output = open("traces_output.txt", 'w')

log_number = 0
# delete duplicates
for log in logs:
    # log = list(dict.fromkeys(log))
    log = del_duplicates(log)

    # sort by time (first part of tuple)
    log = sorted(log, key=lambda x: x[0])
    # deleting all logs with two timeouts in a row
    if not wanna_delete_double_to_log(log):
        log_number += 1
        output.write("log: " + str(log_number) + "\n")
        for i, event in enumerate(log):

            event_string = "<"
            event_string += mapping(event[1]) + "," + str(event[0]) + ">"
            output.write(str(event_string) + "\n")
output.close()

# Post output validations
# output = open("traces_output.txt", 'r')
# logs = []
# lines = [line.replace('\n', '').replace('<', '').replace('>', '') for line in output.readlines()]
#
# # TODO: This value is currently given
# nodes = 3
#
# for index, line in enumerate(lines):
#     # line initializing new event feed for a log (log: x)
#     if line[0] == "l":
#         if index > 0 and skip_flag == False:
#             logs.append(temp)
#         temp = Log()
#         skip_flag = False
#         reqX0_present = []
#         for i in range(nodes):
#             reqX0_present.append(False)
#     else:
#         wholesignal, ts = line.split(',')
#         ts = int(ts)
#         # timeout represented by wildcard '.'
#         if wholesignal != '.':
#             # first 3 characters are Req or Ack
#             signal = wholesignal[:3]
#             origin = int(wholesignal[3])
#             target = int(wholesignal[4])
#             for i in range(nodes):
#                 if signal == "Req" and origin-1 == i:
#                     reqX0_present[i] = True
#                 elif (signal != "Req") and (target-1 == i or origin-1 == i) and (reqX0_present[i] == False):
#                     skip_flag = True
#         else:
#             signal = "."
#             origin = ""
#             target = ""
#         temp.events.append(Event(signal, origin, target, ts))
#
# output.close()
# os.remove("traces_output.txt")
# output = open("traces_output.txt", 'w')
# log_number = 0
# for log in logs:
#     log_number += 1
#     output.write("log: " + str(log_number) + "\n")
#     for i, event in enumerate(log.events):
#         event_string = "<"
#         event_string += event.signal + str(event.origin) + str(event.target) + "," + str(event.ts) + ">"
#         output.write(str(event_string) + "\n")
# output.close()
