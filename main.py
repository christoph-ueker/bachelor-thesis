import subprocess
from helper import *
from uppaalpy import nta as u
import copy
import sys
# https://stackoverflow.com/questions/45012964/stdout-progress-bars-dont-work-in-pycharm
# Required to make the progress bar work TODO: mention this in readme
from alive_progress import alive_bar
import timeit
import random

# initialize interval abstraction parameter
# R = int(input("What should I take for interval abstraction parameter?:\n"))
# os.system('python simulator.py')

print("Main is running now...")
start = timeit.default_timer()

# this suppresses all printing to console, comment out to reactivate
# blockPrint()


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


def new_template(name):
    """Creates new template from blank_template and appends it to sys.templates

    :param str name:    name of the new template
    :return:            new template
    :rtype:             u.Template
    """
    new = copy.deepcopy(blank_template)
    new.name = u.Name(name=name, pos=[0, 0])
    sys.templates.append(new)
    return new


def read_logs(file):
    """Reads logs line-wise from text file into an array

    :param str file: text file containing the logs in a line-wise fashion
    :return: array of logs
    """
    logs = []
    log_file = open(file, "r")
    lines = [line.replace('\n', '').replace('<', '').replace('>', '') for line in log_file.readlines()]

    i = -1
    for index, line in enumerate(lines):
        # line initializing new event feed for a log ("log: x")
        if line[0] == "l":
            logs.append(Log())
            i += 1
        else:
            wholesignal, ts = line.split(',')
            ts = int(ts)
            # timeout represented by 'To'
            if wholesignal[:2] == 'To':
                signal = "---"
                origin = "-"
                target = int(wholesignal[2:])
            else:
                # first 3 characters are Req or Ack
                signal = wholesignal[:3]
                rest = wholesignal[3:]
                origin, target = rest.split('x')
                origin = int(origin)
                target = int(target)
            logs[i].events.append(Event(signal, origin, target, ts))

    log_file.close()

    # randomize the order of logs for experiment in the evaluation part
    # random.shuffle(logs)

    return logs


def new_x(node):
    """Determines x position for a new location

    :param int node:    Template to add the new location
    :return:            new x position
    :rtype:             int
    """
    return step_size * num_locations(node)


def new_id(node):
    """Determines id for a new location

    :param int node:    Template to add the new location
    :return:            new id
    :rtype:             str
    """
    return "id" + str(num_locations(node))


def active_index(node):
    """Determines index for a new active location

    :param int node:    Template to add the new location
    :return:            new active index
    :rtype:             int
    """
    return len(active_locations[node - 1]) + 1


def passive_index(node):
    """Determines index for a new passive location

    :param int node:    Template to add the new location
    :return:            new passive index
    :rtype:             int
    """
    return len(passive_locations[node - 1]) + 1


def all_locations(node):
    """Combines active and passive locations of a node's template

    :param int node:    Template of locations
    :return:            list of all locations
    :rtype:             list of u.Location
    """
    return passive_locations[node - 1] + active_locations[node - 1]


def has_end_loc(node):
    """Checks whether a node's template already has an end location called 'END'

    :param int node:    node to check the template of
    :return:            true if it has 'END' location
    :rtype:             bool
    """
    for location in all_locations(node):
        if location.name.name == "END":
            return True
    return False


def get_end_loc(node):
    """Retrieves the end location of a node's template

    :param int node:    node to retrieve the end location of
    :return:            end location
    :rtype:             u.Location
    """
    if not has_end_loc(node):
        raise LookupError('There is no end location for this node!')
    for location in all_locations(node):
        if location.name.name == "END":
            return location


def new_channel(ori, tar, name, suffix):
    """Adds new transition to SUT (if the channel is new), adds channel to used channels,
    determines label for Env transition

    :param u.Location ori:  origin of the channel's transition
    :param u.Location tar:  target of the channel's transition
    :param str name:        channel's name
    :param str suffix:      either '?' or '!'
    :return:                label for the Env channel
    :rtype:                 u.Label
    """
    # BLOCK for Env Channel
    label = u.Label(kind="synchronisation", pos=sync_label_pos(ori, tar),
                    value=name + suffix)
    # print("Creating Channel: " + name + suffix)

    # BLOCK for adding transition to SUT, if new Channel
    if suffix == "?":
        inverse = name + "!"
    elif suffix == "!":
        inverse = name + "?"
    else:
        raise AssertionError("Wrong suffix for channel creation!")

    if name not in channels:
        channels.append(name)

    # TODO: Proper positioning of self-edges and labels for SUT (maybe even dynamic readjusting)
    # old ones to fit in a circle -> make it scalable
    # use nails, put label between nails
    if inverse not in sut_channels:
        sut_channels.append(inverse)
        sut_label = u.Label(kind="synchronisation", pos=sync_label_pos(sut_loc, sut_loc),
                            value=inverse)
        trans = u.Transition(source=sut_loc.id, target=sut_loc.id, synchronisation=sut_label)
        sut.add_trans(trans)
        # @see arrange_sut_edges
    return label


def add_qual_trans(node, src, tar, guard, comments, **kwargs):
    """
    Adds a new transition to a node's template

    :param int node:            Template to add the transition to
    :param u.Location src:      source location
    :param u.Location tar:      target location
    :param int guard:           guard values
    :param str comments:        comments
    :kwarg [int, int] nails:    position tuple for a u.Nail
    :kwarg str sync:            synchronisation Channel Label
    :kwarg str guard_string:    used  for timeout transitions to state '=='
    :return:                    new transition
    :rtype:                     u.Transition
    """

    guard_string = kwargs.get('guard_string')
    if guard_string is None:
        guard_string = "cl>="
    guard_label = u.Label(kind="guard", pos=guard_label_pos(src, tar),
                          value=guard_string + str(guard))
    # the standard assignment for every transition 'cl=0'
    assignment_label = u.Label(kind="assignment",
                               pos=asgn_label_pos(src, tar), value="cl=0")
    comment = u.Label(kind="comments", pos=asgn_label_pos(src, tar),
                      value=comments)
    trans = u.Transition(source=src.id, target=tar.id, guard=guard_label,
                         assignment=assignment_label, comments=comment)
    # print("[" + templ.name.name + "] Adding transition from: " + src.name.name + " to: " + tar.name.name)
    # TODO: maybe add array of nails
    nails = kwargs.get('nails')
    if nails is not None:
        nail = u.Nail(pos=[nails[0], nails[1]])
        trans.nails = [nail]
    sync = kwargs.get('sync')
    if sync is not None:
        if sync.value[0:3] == "Ack":
            # Assumption: After acknowledgment we are done with that Node
            if has_end_loc(node) and tar != get_end_loc(node):
                # redirect transition to end location as target
                env[node - 1].del_loc(trans.target)
                trans.target = get_end_loc(node).id
            else:
                target = get_loc_by_id(all_locations(node), tar.id)
                # print("SETTING END LOCATION")
                target.name.name = "END"
        trans.synchronisation = sync
    env[node - 1].add_trans(trans)
    return trans


def interval_extension(lb, ub, r):
    """Calculating new lower and upper bound by applying the mathematical interval extension

    :param int lb:  initial lower bound
    :param int ub:  initial upper bound
    :param int r:   interval extension parameter to be used
    :return:        new lower and upper bound
    :rtype:         (int, int)
    """
    delta = (r - (ub - lb))/2
    # TODO: Check whether this is valid
    # we only EXTEND the interval
    if delta > 0:
        new_lb = lb - delta
        new_ub = ub + delta
        return new_lb, new_ub
    else:
        return lb, ub


def get_loc_by_id(loc_list, id):
    """Retrieves the location behind an id

    :param list of u.Location loc_list: list of locations to look through
    :param string id:                   id to look after
    :return:                            location behind the given id
    :rtype:                             u.Location
    """
    for loc in loc_list:
        if loc.id == id:
            return loc
    return "Error while looking for id: " + id


def in_target_locs(loc, transitions):
    """Checks whether a location is in the targets of a list of transitions

    :param u.Location loc:                      location to be checked
    :param list of u.Transition transitions:    list of transitions to be checked
    :return:                                    whether the location is in the targets
    :rtype:                                     bool
    """
    for trans in transitions:
        if trans.target == loc.id:
            return True
    return False


def in_target_locs_guard(loc, guard_val, transitions):
    """Checks whether a list of transition has a transition with a specific value

    :param u.Location loc:                      location to be checked
    :param int guard_val:                       value of the guard to be checked
    :param list of u.Transition transitions:    list of transitions to be checked
    :return:                                    whether a guard value is in the guards
    :rtype:                                     bool
    """
    for trans in transitions:
        if trans.target == loc.id:
            s = trans.guard.value
            if s[s.rfind("=="):] == "==" + str(guard_val):
                return True
    return False


def num_locations(node):
    """Determines the number of locations for a specific node

    :param int node:    number of node
    :return:            number of locations for a specific node
    :rtype:             int
    """
    return len(active_locations[node - 1]) + len(passive_locations[node - 1])


def new_loc_name(loc_type, index):
    """

    :param str loc_type:    either "a" for active or "p" for passive
    :param int index:       index of the specific location set (active or passive)
    :return:                name for the new location
    :rtype:                 str
    """
    name = "L" + loc_type + str(index)
    # print("New loc name: " + name)
    return name


for r in range(1, 20):
    R = r

    """ --- MAJOR INITIALISATIONS --- """

    # load the blank system generated by UPPAAL as a starting point
    sys = u.NTA.from_xml(path='xml-files/blank_system.xml')
    sys.templates[0].graph.remove_node(('Template', 'id0'))
    blank_template = copy.deepcopy(sys.templates[0])
    sys.templates.pop()

    sut = new_template("SUT")
    # test = new_template()
    env = []  # list of templates for the Env nodes
    sut_channels = []  # store used Channel names of SUT
    channels = []  # store used channels to write them to UPPAAL global declarations

    step_size = 200  # step size for locations
    active_locations = []
    passive_locations = []

    # SUT has only one location
    sut_loc = sut.add_loc(u.Location(id="id0", pos=[0, 0]))

    logs = read_logs("traces_output.txt")
    # put = (0, 0, 0)

    # with alive_bar(20000) as bar:  # declare your expected total
    #     for i in range(20000):
    #         x = 10 + 4
    #         bar()                  # call `bar()` at the end

    # iterate over all logs

    with alive_bar(total=len(logs), title='Iterating logs', force_tty=True, bar='smooth') as bar:
        for count, log in enumerate(logs):
            # print("\nLog: " + str(count+1))
            # if put != (1, 1, 1):
            #     put = proceeding(count, len(logs), put)

            # setup everything
            if count == 0:
                # count the Env Nodes, assumption: it has to be the same for all logs
                number_env_nodes = 0
                for event in log.events:
                    # ignore timeouts
                    if event.signal != "---":
                        if event.origin > number_env_nodes:
                            number_env_nodes = event.origin
                        if event.target > number_env_nodes:
                            number_env_nodes = event.target

                # create new template for Env Node
                for i in range(1, number_env_nodes + 1):
                    env.append(new_template("Node" + str(i)))

                # create clock declaration for every Env Template
                for node in env:
                    node.declaration = u.Declaration("clock cl;")

            """ --- BEGIN INITIALIZATIONS --- """

            # initialize internal clocks
            internal_clock = []
            for i in range(1, number_env_nodes + 1):
                internal_clock.append(0)

            # other initializations
            timeout_ts = []
            timeout_units = []
            working_loc = []

            # intialize arrays with length being the number of Env nodes, so you can access specific traits for them by index
            for i in range(number_env_nodes):
                active_locations.append([])
                passive_locations.append([])
                timeout_ts.append(0)
                timeout_units.append(0)
                # some random initial location
                working_loc.append(u.Location(id="id1337", pos=[0, 0], name=u.Name("1337", pos=[0, 0])))

            # if we are not in the first log, we set the working location for each node to the initial location
            if count > 0:
                for i in range(number_env_nodes):
                    working_loc[i] = get_loc_by_id(all_locations(i + 1), env[i].graph.initial_location[1])

            """ --- END INITIALIZATIONS --- """

            # iterate over all events in a log
            for event_index, event in enumerate(log.events):
                # Env event
                if event.type == "Env":
                    signal = event.signal + str(event.origin) + "x" + str(event.target)
                    # print("Env Event: " + signal)

                    proc = event.origin
                    clock = event.ts - internal_clock[proc - 1]
                    internal_clock[proc - 1] = event.ts
                    init_loc = get_loc_by_id(all_locations(proc), env[proc - 1].graph.initial_location[1])

                    """ --- BEGIN TIMEOUT HANDLING --- """

                    # last event was timeout, we have to go to initial location by assumption
                    if timeout_ts[proc - 1] != 0:
                        clock = internal_clock[proc - 1] - timeout_ts[proc - 1]
                        # if clock == 4:
                            # forcePrint("Log is:" + str(count+2))
                        # print("timeout handling")

                        # there is no invariant in the working location yet
                        if not hasattr(working_loc[proc - 1].invariant, 'value'):
                            # We have to create invariant for this location
                            working_loc[proc - 1].invariant = u.Label(kind="invariant", pos=[last_loc.pos[0], 20],
                                                                      value="cl<=" + str(clock))
                            inv_ub = 0
                        else:
                            inv_ub = int(working_loc[proc - 1].invariant.value[4:])
                        working_loc[proc - 1].invariant.value = "cl<=" + str(max(timeout_units[proc - 1], inv_ub))

                        if not in_target_locs_guard(init_loc, timeout_units[proc - 1],
                                                    env[proc - 1].get_trans_by_source(working_loc[proc - 1])):
                            add_qual_trans(node=proc, src=working_loc[proc - 1], tar=init_loc, guard=timeout_units[proc - 1],
                                           comments="timeout", guard_string="cl==")  # nails=[-30, -30],
                            # reposition last location
                            repos_loc(working_loc[proc - 1], init_loc.pos[0], init_loc.pos[1] + step_size)
                        working_loc[proc - 1] = init_loc
                        timeout_ts[proc - 1] = 0

                    """ --- END TIMEOUT HANDLING --- """

                    # Check the condition for Case 1
                    cond = False

                    # TODO: Check whether this is fine, as it is different to paper
                    # going through all transitions with source being the location we are currently in
                    source_loc = working_loc[proc - 1]
                    # print("Working loc is: " + working_loc[proc - 1].name.name)
                    for transition in env[proc - 1].get_trans_by_source(working_loc[proc - 1]):

                        guard_lb = int(transition.guard.value[4:])
                        target_loc = get_loc_by_id(passive_locations[proc - 1], transition.target)
                        if hasattr(source_loc.invariant, 'value'):
                            inv_ub = int(source_loc.invariant.value[4:])
                        else:
                            inv_ub = guard_lb
                        lb, ub = interval_extension(guard_lb, inv_ub, R)
                        if hasattr(transition.synchronisation, 'value'):
                            if signal + "!" == transition.synchronisation.value and lb <= clock <= ub:
                                cond = True
                                found_trans = transition
                                break

                    # Case 1
                    if cond:
                        # print("Env Case 1 for " + str(env[proc - 1].name.name))

                        # forcePrint("log: " + str(count+1) + " --- " + str(inv_ub) + ", " + str(clock))
                        # update corresponding guard
                        found_trans.guard.value = "cl>=" + str(min(clock, guard_lb))
                        # update corresponding invariant
                        if hasattr(source_loc.invariant, 'value'):
                            source_loc.invariant.value = "cl<=" + str(max(clock, inv_ub))
                        else:
                            position = [source_loc.pos[0], source_loc.pos[1]]
                            source_loc.invariant = u.Label(kind="invariant",
                                                           pos=inv_loc_pos(position[0], position[1]),
                                                           value="cl<=" + str(max(clock, inv_ub)))

                        working_loc[proc - 1] = target_loc

                    # Case 2
                    else:
                        # print("Env Case 2 for " + str(env[proc - 1].name.name))

                        if active_index(proc) > 1:  # If not first active location
                            working_active_loc = active_locations[proc - 1][-1]  # This considers the top of the stack
                        else:  # If first active location
                            # add location to the active locations
                            position = [new_x(proc), 0]
                            new_active = u.Location(id=new_id(proc), pos=position,
                                                    name=u.Name(new_loc_name(loc_type="a", index=active_index(proc)),
                                                                pos=name_loc_pos(position[0], position[1])),
                                                    invariant=u.Label(kind="invariant",
                                                                      pos=inv_loc_pos(position[0], position[1]),
                                                                      value="cl<=" + str(clock)))
                            active_locations[proc - 1].append(env[proc - 1].add_loc(new_active))
                            working_active_loc = new_active

                        if has_end_loc(proc):
                            end_loc = get_end_loc(proc)
                            if not in_target_locs(end_loc, env[proc - 1].get_trans_by_source(working_active_loc)):
                                add_qual_trans(node=proc, src=working_active_loc, tar=end_loc, guard=clock,
                                               comments="controllable",
                                               sync=new_channel(working_active_loc, end_loc, signal, "!"))
                                working_active_loc.invariant = u.Label(kind="invariant",
                                                                       pos=inv_loc_pos(working_active_loc.pos[0],
                                                                                       working_active_loc.pos[1]),
                                                                       value="cl<=" + str(clock))
                            working_loc[proc - 1] = end_loc
                        else:
                            # add location to the passive locations
                            position = [new_x(proc), 0]
                            new_passive = u.Location(id=new_id(proc), pos=position,
                                                     name=u.Name(new_loc_name(loc_type="p", index=passive_index(proc)),
                                                                 pos=name_loc_pos(position[0], position[1])))
                            passive_locations[proc - 1].append(env[proc - 1].add_loc(new_passive))
                            working_loc[proc - 1] = new_passive
                            # add transition
                            add_qual_trans(node=proc, src=working_active_loc, tar=new_passive, guard=clock,
                                           comments="controllable",
                                           sync=new_channel(working_active_loc, new_passive, signal, "!"))
                # SUT Event
                else:
                    signal = event.signal + str(event.origin) + "x" + str(event.target)
                    # print("SUT Event: " + signal)

                    proc = event.target
                    if event.origin == "-":
                        # print("timeout event, skipping...")
                        timeout_ts[proc - 1] = event.ts

                        # accessing predecessor event involving that process
                        temp_target = 1
                        temp_origin = 1
                        for i in range(1, 1000000):
                            if log.events[event_index - i].target == proc:
                                temp_target = i
                                break
                        for i in range(1, 1000000):
                            if log.events[event_index - i].origin == proc:
                                temp_origin = i
                                break
                        if temp_target < temp_origin:
                            temp = temp_target
                        else:
                            temp = temp_origin
                        timeout_units[proc - 1] = timeout_ts[proc - 1] - log.events[event_index - temp].ts
                        # if timeout_units[proc - 1] == 9:
                        #     forcePrint(count)
                        # print("TIMEOUT UNITS = " + str(timeout_units[proc - 1]))
                        continue
                    clock = event.ts - internal_clock[proc - 1]
                    internal_clock[proc - 1] = event.ts
                    last_loc = working_loc[proc - 1]
                    init_loc = get_loc_by_id(all_locations(proc), env[proc - 1].graph.initial_location[1])
                    # print("Working loc is: " + working_loc[proc - 1].name.name)

                    """ --- BEGIN TIMEOUT HANDLING --- """

                    # last event was timeout
                    if timeout_ts[proc - 1] != 0:
                        # TODO: Revision this, this is never used due to assumptions
                        clock = internal_clock[proc - 1] - timeout_ts[proc - 1]

                        # forcePrint("timeout handling for SUT")

                        # there is no invariant in the working location yet
                        if not hasattr(working_loc[proc - 1].invariant, 'value'):
                            # We have to create invariant for this location
                            working_loc[proc - 1].invariant = u.Label(kind="invariant", pos=[last_loc.pos[0], 20],
                                                                      value="cl<=" + str(clock))
                            inv_ub = 0
                        else:
                            inv_ub = int(working_loc[proc - 1].invariant.value[4:])
                        working_loc[proc - 1].invariant.value = "cl<=" + str(max(timeout_units[proc - 1], inv_ub))

                        if not in_target_locs_guard(init_loc, timeout_units[proc - 1],
                                                    env[proc - 1].get_trans_by_source(working_loc[proc - 1])):
                            add_qual_trans(node=proc, src=working_loc[proc - 1], tar=init_loc, guard=timeout_units[proc - 1],
                                           comments="timeout", guard_string="cl==")  # nails=[-30, -30],
                            # reposition last location
                            repos_loc(working_loc[proc - 1], init_loc.pos[0], init_loc.pos[1] + step_size)
                        working_loc[proc - 1] = init_loc
                        timeout_ts[proc - 1] = 0
                        last_loc = working_loc[proc - 1]

                    """ --- END TIMEOUT HANDLING --- """

                    # Check the condition for Case 1
                    cond = False
                    for transition in env[proc - 1].get_trans_by_source(working_loc[proc - 1]):
                        guard_lb = int(transition.guard.value[4:])
                        source_loc = source_loc = working_loc[proc - 1]
                        target_loc = get_loc_by_id(all_locations(proc), transition.target)
                        if hasattr(source_loc, 'invariant'):
                            if source_loc.invariant is not None:
                                inv_ub = int(source_loc.invariant.value[4:])
                        else:
                            inv_ub = clock
                        lb, ub = interval_extension(guard_lb, inv_ub, R)
                        if hasattr(transition.synchronisation, 'value'):
                            # print("SIGNAL: " + signal + "?, SYNC VAL: " + transition.synchronisation.value)
                            # print("lb: " + str(lb) + ", clock: " + str(clock) + ", ub: " + str(ub))
                            if signal + "?" == transition.synchronisation.value and lb <= clock <= ub:
                                cond = True
                                found_trans = transition
                                break

                    # Case 1
                    if cond:
                        # print("SUT Case 1 for " + str(env[proc - 1].name.name))
                        # update corresponding guard
                        found_trans.guard.value = "cl>=" + str(min(clock, guard_lb))
                        # update corresponding invariant
                        if not hasattr(source_loc, 'invariant'):
                            source_loc.invariant = u.Label(kind="invariant",
                                                           pos=inv_loc_pos(source_loc.pos[0], source_loc.pos[1]))
                        source_loc.invariant.value = "cl<=" + str(max(clock, inv_ub))
                        working_loc[proc - 1] = target_loc

                    # Case 2
                    else:
                        # print("SUT Case 2 for " + str(env[proc - 1].name.name))
                        if hasattr(last_loc.invariant, 'value'):
                            inv_ub = int(last_loc.invariant.value[4:])
                        else:
                            # We have to create invariant for this location first
                            last_loc.invariant = u.Label(kind="invariant", pos=inv_loc_pos(last_loc.pos[0], last_loc.pos[1]),
                                                         value="cl<=" + str(clock))
                            inv_ub = clock

                        last_loc.invariant.value = "cl<=" + str(max(clock, inv_ub))
                        # add location to the active locations
                        position = [new_x(proc), 0]
                        new_active = u.Location(id=new_id(proc), pos=position,
                                                name=u.Name(new_loc_name(loc_type="a", index=active_index(proc)),
                                                            pos=name_loc_pos(position[0], position[1])))
                        active_locations[proc - 1].append(env[proc - 1].add_loc(new_active))

                        working_active_loc = new_active
                        working_loc[proc - 1] = new_active
                        # add transition
                        add_qual_trans(node=proc, src=last_loc, tar=working_active_loc, guard=clock,
                                       comments="observable", sync=new_channel(last_loc, working_active_loc, signal, "?"))
            bar()

    # --- Finishing Ops ---

    # post-processing
    node_count = 10.00
    total_loc_count = 0.00
    total_edge_count = 0.00
    # insert nail in the middle of all transitions
    for i, node in enumerate(env):
        transitions = node.get_edges()
        locations = node.get_nodes()
        total_loc_count += float(len(locations))
        total_edge_count += float(len(transitions))
        for trans in transitions:
            pos = middle_nail_pos(
                get_loc_by_id(locations, trans.source), get_loc_by_id(locations, trans.target))
            # print(pos)
            if pos != 1:
                middle_nail = u.Nail(pos=pos)
                trans.nails = [middle_nail]

    # write global declarations
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
    sys.to_file(path='xml-files/output.xml', pretty=True)

    stop = timeit.default_timer()
    # print("Total runtime of the algorithm: ", stop - start, "seconds")
    # enablePrint()
    # print("UPPAAL is running now...")

    # run UPPAAL and suppressing its output
    # running_uppaal = subprocess.call(['java', '-jar', 'UPPAAL-Stratego/uppaal.jar', 'xml-files/output.xml'],
    #                                  stdout=subprocess.DEVNULL,
    #                                  stderr=subprocess.STDOUT)

    forcePrint("R= " + str(R) + ", Avg Locs: " + str(float(total_loc_count / node_count)) + ", Avg Edges: "
               + str(float(total_edge_count / node_count)))
