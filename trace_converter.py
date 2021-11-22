import copy
# number of simulations
sim_count = 0
with open("traces.txt") as trace_file:
    lines = trace_file.readlines()

    # save lines to array
    lines = [line.rstrip() for line in lines]

    # read number of simulations from first line
    temp = lines[0]
    sim_count = int(temp[temp.rfind("(") + 1:temp.rfind(")"):])

    copy = copy.deepcopy(lines)
    lines = []
    for index, line in enumerate(copy):
        # only keep useful lines
        if line[0] not in ["0", "#"]:
            lines.append(line)
    print(lines)

trace_file.close()

# if temp[0] not in ['#', '0']:

# for line in trace_file:
#     temp = line.rstrip()
#     if temp[:4] == "####":
#         # read number of simulations from first line, starting with "####"
#         sim_count = int(temp[temp.rfind("(") + 1:temp.rfind(")"):])
#     else:
#         print(temp)
