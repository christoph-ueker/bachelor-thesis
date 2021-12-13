import sys
import os
from uppaalpy import nta as u

""" BEGIN GENERAL HELPER FUNCTIONS """


def blockPrint():
    """Disable printing to console
    """
    sys.stdout = open(os.devnull, 'w')


def enablePrint():
    """Restore printing to console
    """
    sys.stdout = sys.__stdout__


""" END GENERAL HELPER FUNCTIONS """

""" BEGIN POSITIONAL HELPER FUNCTIONS """


def middle_nail_pos(src, tar):
    return int((src.pos[0] + tar.pos[0]) / 2), int((src.pos[1] + tar.pos[1]) / 2)


# same as nail position
def guard_label_pos(src, tar):
    """Determines the position for the guard label of a transition

    :param u.Location src:  source location
    :param u.Location tar:  target location
    :return:                position tuple
    :rtype:                 tuple of int
    """
    return (src.pos[0] + tar.pos[0]) / 2, (src.pos[1] + tar.pos[1]) / 2


def asgn_label_pos(src, tar):
    """Determines the position for the assignment label of a transition

    :param u.Location src:  source location
    :param u.Location tar:  target location
    :return:                position tuple
    :rtype:                 tuple of int
    """
    return [(src.pos[0] + tar.pos[0]) / 2 + 5, (src.pos[1] + tar.pos[1]) / 2]


def sync_label_pos(src, tar):
    """Determines the position for the synchronisation label of a transition

    :param u.Location src:  source location
    :param u.Location tar:  target location
    :return:                position tuple
    :rtype:                 tuple of int
    """
    return [(src.pos[0] + tar.pos[0]) / 2 + 10, (src.pos[1] + tar.pos[1]) / 2]


def comment_label_pos(src, tar):
    """Determines the position for the comment label of a transition

    :param u.Location src:  source location
    :param u.Location tar:  target location
    :return:                position tuple
    :rtype:                 tuple of int
    """
    return [(src.pos[0] + tar.pos[0]) / 2 + 10, (src.pos[1] + tar.pos[1]) / 2 + 5]


def name_loc_pos(loc_x, loc_y):
    """Determines the position for the name of a location

    :param int loc_x:   x coordinate of the location
    :param int loc_y:   y coordinate of the location
    :return:            position tuple
    :rtype:             tuple of int
    """
    return [loc_x + 7, loc_y + 7]


def inv_loc_pos(loc_x, loc_y):
    """Determines the position for the invariant of a location

    :param int loc_x:   x coordinate of the location
    :param int loc_y:   y coordinate of the location
    :return:            position tuple
    :rtype:             tuple of int
    """
    return [loc_x + 7, loc_y + 20]


def repos_loc(loc, x_pos, y_pos):
    """Repositions a location and its Labels to a new position

    :param u.Location loc:  location to be repositioned
    :param int x_pos:       new x coordinate
    :param int y_pos:       new y coordinate
    :return:                repositioned location
    :rtype:                 u.Location
    """
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
