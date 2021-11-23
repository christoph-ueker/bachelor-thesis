"""
This module converts the export text file from a UPPAAL simulation to
the used log format in the main module.
Performant for at least 10000 logs.
"""

import math


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
        signal = "Req" + str(math.floor(number/6) + 1) + "0"
    if number % 8 == 1:
        signal = "Ack" + "0" + str(math.floor(number / 6) + 1)
    if number % 8 in [2, 6, 7]:
        signal = "Req" + "0" + str(math.floor(number / 6) + 1)
    if number % 8 == 3:
        signal = "Ack" + str(math.floor(number / 6) + 1) + "0"
    if number % 8 == 4:
        signal = "."
        # signal = "TO" + str(math.floor(number / 6) + 1) + "0"
    if number % 8 == 5:
        signal = "."
        # signal = "TO" + str(math.floor(number / 6) + 1) + "00"
    return signal

# deletes every second line, as they are duplicates from UPPAAL
def del_duplicates(arr):
    temp = []
    for i, sth in enumerate(arr):
        if arr[i][1] != arr[i-1][1]:
            temp.append(arr[i])
    return temp


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
for i in range(sim_count-1):
    arranged_logs.append([])
for i in range(sim_count):
    for j in range(node_count):
        arranged_logs[i] += logs[i+j*sim_count]

logs = [[]]
for i in range(sim_count-1):
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

# delete duplicates
for num, log in enumerate(logs):
    output.write("log: " + str(num+1) + "\n")
    log = del_duplicates(log)
    log = list(dict.fromkeys(log))
    # sort by time (first part of tuple)
    log = sorted(log, key=lambda x: x[0])
    for event in log:
        event_string = "<"
        event_string += mapping(event[1]) + "," + str(event[0]) + ">"
        output.write(str(event_string) + "\n")
output.close()
