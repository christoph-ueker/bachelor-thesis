""" POSITIONAL HELPER FUNCTIONS """


def guard_label_pos(ori, tar):
    return [(ori.pos[0] + tar.pos[0]) / 2, (ori.pos[1] + tar.pos[1]) / 2]


def asgn_label_pos(ori, tar):
    return [(ori.pos[0] + tar.pos[0]) / 2 + 5, (ori.pos[1] + tar.pos[1]) / 2]


def sync_label_pos(ori, tar):
    return [(ori.pos[0] + tar.pos[0]) / 2 + 10, (ori.pos[1] + tar.pos[1]) / 2]


def comment_label_pos(ori, tar):
    return [(ori.pos[0] + tar.pos[0]) / 2 + 10, (ori.pos[1] + tar.pos[1]) / 2 + 5]


# returns the position for the name of a location
def name_loc_pos(loc_x, loc_y):
    return [loc_x + 7, loc_y + 7]


# returns the position for the invariant of a location
def inv_loc_pos(loc_x, loc_y):
    return [loc_x + 7, loc_y + 20]


# repositions a location and its Labels to a new position
def repos_loc(loc, x_pos, y_pos):
    print("repositioning " + loc.name.name)
    loc.pos = [x_pos, y_pos]
    loc.name.pos = name_loc_pos(x_pos, y_pos)
    loc.invariant.pos = inv_loc_pos(x_pos, y_pos)
    return loc


# TODO: finish this
def arrange_sut_edges(sut):
    all_edges = sut.get_trans_by_source(sut.graph.initial_location)
    num_edges = len(all_edges)
    for i in range(num_edges):
        all_edges[i].nails = NotImplemented
        # we need nail position function depending on number of edges -> circle around sut
