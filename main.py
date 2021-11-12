import os
from helper import *
from uppaalpy import nta as u
import copy


# creates a new template from blank_template
def new_template(name):
    new = copy.deepcopy(blank_template)
    new.name = u.Name(name=name, pos=[0, 0])
    sys.templates.append(new)
    return new


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


# TODO: Change this in case the log file format is adjusted
# TODO: Currently the format only fits for <10 Env Nodes -> Scalability
# filename: "logs/log1.txt"
def read_log_from_file(file):
    log_file = open(file, "r")
    lines = [line.replace('\n', '').replace('<', '').replace('>', '') for line in log_file.readlines()]
    # print(lines)
    log = Log()
    for line in lines:
        wholesignal, ts = line.split(',')
        ts = int(ts)
        # timeout represented by wildcard '.'
        if wholesignal == '.':
            signal = "---"
            origin = "-"
            target = "-"
        else:
            # first 3 characters are Req or Ack
            signal = wholesignal[:3]
            origin = int(wholesignal[3])
            target = int(wholesignal[4])
        # print(signal + " " + origin + " " + target + " " + str(ts))
        log.events.append(Event(signal, origin, target, ts))
    log_file.close()
    return log


def new_x(node):
    return stepsize * num_locations(node)


def new_id(node):
    return "id" + str(num_locations(node))


# my_log = read_log_from_file("logs/log1.txt")
# print(my_log)

# --- BEGIN my_alg ---

# load the blank system generated by UPPAAL as a starting point
sys = u.NTA.from_xml(path='blank_system.xml')
sys.templates[0].graph.remove_node(('Template', 'id0'))
blank_template = copy.deepcopy(sys.templates[0])
sys.templates.pop()

# creates new template for SUT
sut = new_template("SUT")
env = []

# store used Channel names of SUT
sut_channels = []
# store used Channel names in general of adding to declarations
channels = []

#
stepsize = 200  # stepsize for locations
last_locations = [] # last used locations
active_locations = []


def active_index(node):
    return len(active_locations[node - 1]) + 1


passive_locations = []


def passive_index(node):
    return len(passive_locations[node - 1]) + 1


# adds transition to SUT (if new), adds to used channels, determines label for Env transition
def new_channel(value, suffix):
    # BLOCK for Env Channel
    label = u.Label(kind="synchronisation", pos=sync_label_pos(working_active_loc, new_passive),
                    value=value + suffix)

    # BLOCK for adding transition to SUT, if new Channel
    if suffix == "?":
        inverse = value + "!"
    elif suffix == "!":
        inverse = value + "?"
    else:
        inverse = None
        print("WRONG SUFFIX FOR CHANNEL CREATION")

    # store used channels to write them to UPPAAL global declarations
    if value not in channels:
        channels.append(value)

    # TODO: Proper positioning of self-edges and labels for SUT (maybe even dynamic readjusting
    # old ones to fit in a circle -> make it scalable
    if inverse not in sut_channels:
        sut_channels.append(inverse)
        sut_label = u.Label(kind="synchronisation", pos=sync_label_pos(sut_loc, sut_loc),
                            value=inverse)
        trans = u.Transition(source=sut_loc.id, target=sut_loc.id, synchronisation=sut_label)
        sut.add_trans(trans)
    return label


def interval_extension(lb, ub, r):
    delta = r - (ub - lb)
    new_lb = lb - delta
    new_ub = ub + delta
    return new_lb, new_ub


def get_loc_by_id(loc_list, id):
    for loc in loc_list:
        if loc.id == id:
            return loc
    return "ERROR"


# this is how we add locations
sut_loc = sut.add_loc(u.Location(id="id0", pos=[0, 0]))

# iterate over the files in logs folder
for filename in os.listdir("logs"):
    log = read_log_from_file("logs/" + filename)

    # TODO: This assumption is fine for now, Iam assuming it
    # count the Env Nodes, it has to be the same for all logs
    number_env_nodes = 0
    for event in log.events:
        # ignore timeouts
        if event.signal != "---":
            if event.origin > number_env_nodes or event.target > number_env_nodes:
                number_env_nodes = event.origin

    # create new template for Env Node, if we have none yet
    if not env:
        for i in range(1, number_env_nodes + 1):
            env.append(new_template("Node" + str(i)))

    # create clock declaration for every Env Template
    for node in env:
        node.declaration = u.Declaration("clock cl;")

    """ --- BEGIN INITIALIZATIONS --- """

    # initialize internal clocks and interval abstraction parameter
    internal_clock = []
    for i in range(1, number_env_nodes + 1):
        internal_clock.append(0)
    R = 4
    # other initializations
    timeout_ts = 0

    # returns the number of locations for a specific node
    def num_locations(node):
        return len(active_locations[node - 1]) + len(passive_locations[node - 1])


    def new_loc_name(loc_type, index):
        return "L" + loc_type + str(index)


    for i in range(1, number_env_nodes + 1):
        active_locations.append([])
        passive_locations.append([])

    """ --- END INITIALIZATIONS --- """

    # iterate over all events in a log
    for event in log.events:
        # Env event
        if event.type == "Env":
            signal = event.signal + str(event.origin) + str(event.target)
            origin = event.origin
            clock = event.ts - internal_clock[origin - 1]
            internal_clock[origin - 1] = event.ts

            # TODO: Do the timeout stuff
            # if timeout_ts != 0:
            #     clock = internal_clock[origin - 1] - timeout_ts

            # Check the condition for Case 1
            cond = False
            for transition in env[origin - 1].get_trans_by_comment("controllable"):
                # TODO: Maybe dont use int here
                guard_lb = int(transition.guard.value[4:])
                source_loc = get_loc_by_id(active_locations[origin - 1], transition.source)
                inv_ub = int(source_loc.invariant.value[4:])
                lb, ub = interval_extension(guard_lb, inv_ub, R)
                if signal + "!" == transition.synchronisation.value and lb <= clock <= ub:
                    cond = True
                    found_trans = transition
                    break

            # Case 1
            if cond:
                # update corresponding guard
                found_trans.guard.value = "cl>=" + str(min(clock, guard_lb))
                # update corresponding invariant
                source_loc.invariant.value = "cl<=" + str(max(clock, inv_ub))

            # Case 2, TODO: Review this section
            else:
                if active_index(origin) > 1:  # If not first active location
                    working_active_loc = last_locations[-1]  # This considers the top of the stack
                else:  # If first active location
                    # add location to the active locations
                    new_active = u.Location(id=new_id(origin), pos=[new_x(origin), 0],
                                            name=u.Name(new_loc_name(loc_type="a", index=active_index(origin)),
                                                        pos=[new_x(origin), 0]),
                                            invariant=u.Label(kind="invariant", pos=[new_x(origin), 20],
                                                              value="cl<=" + str(clock)))
                    active_locations[origin - 1].append(env[origin - 1].add_loc(new_active))
                    last_locations.append(new_active)
                    working_active_loc = new_active

                # add location to the passive locations
                new_passive = u.Location(id=new_id(origin), pos=[new_x(origin), 0],
                                         name=u.Name(new_loc_name(loc_type="p", index=passive_index(origin)),
                                                     pos=[new_x(origin), 0]))
                passive_locations[origin - 1].append(env[origin - 1].add_loc(new_passive))
                last_locations.append(new_passive)
                # add transition

                guard_label = u.Label(kind="guard", pos=guard_label_pos(working_active_loc, new_passive),
                                      value="cl>=" + str(clock))
                assignment_label = u.Label(kind="assignment",
                                           pos=asgn_label_pos(working_active_loc, new_passive), value="cl=0")
                sync_label = new_channel(signal, "!")
                # TODO: review positioning
                comment = u.Label(kind="comments", pos=[0, 0], value="controllable")
                trans = u.Transition(source=working_active_loc.id, target=new_passive.id, guard=guard_label,
                                     assignment=assignment_label, synchronisation=sync_label, comments=comment)
                env[origin - 1].add_trans(trans)

        # TODO: SUT Event
        else:
            print("SUT Event detected")
            last = last_locations[-1]
            next_to_last = last_locations[-2]
            signal = event.signal + str(event.origin) + str(event.target)
            target = event.target
            clock = event.ts - internal_clock[target - 1]
            internal_clock[target - 1] = event.ts

            # TODO: Do the timeout stuff

            # Check the condition for Case 1
            cond = False

            # Case 1
            if cond:
                NotImplemented

            # Case 2
            else:
                NotImplemented

# --- Finishing Ops ---

# testwise addition of locations
# for node in env:
#     node.add_loc(u.Location(id="id0", pos=[0, 0], name="La1"))
#     node.add_loc(u.Location(id="id1", pos=[200, 200]))

# write declarations
declarations = "// Place global declarations here.\n"
if channels:
    declarations += "chan "
    for i, channel in enumerate(channels):
        if i == 0:
            declarations += channel
        else:
            declarations += ", " + channel
    declarations += ";"
sys.declaration = u.Declaration(declarations)

# instantiate the templates as processes
template_instantiations = "// Place template instantiations here.\n"
template_instantiations += "NODE0 = " + sut.name.name + "();\n"
for i, template in enumerate(env):
    template_instantiations += "NODE" + str(i + 1) + " = " + template.name.name + "();\n"

# add processes to system
system_processes = "// List one or more processes to be composed into a system.\nsystem "
system_processes += sut.name.name
for i, template in enumerate(env):
    system_processes += ", " + template.name.name
system_processes += ";"

# write system declarations
system_declarations = template_instantiations + system_processes
sys.system = u.SystemDeclaration(system_declarations)

# save the system to xml
sys.to_file(path='output.xml', pretty=True)
