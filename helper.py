""" POSITIONAL HELPER FUNCTIONS """


def guard_label_pos(ori, tar):
    return [(ori.pos[0] + ori.pos[1]) / 2, (tar.pos[0] + tar.pos[1]) / 2]


def asgn_label_pos(ori, tar):
    return [(ori.pos[0] + ori.pos[1]) / 2 + 5, (tar.pos[0] + tar.pos[1]) / 2]


def sync_label_pos(ori, tar):
    return [(ori.pos[0] + ori.pos[1]) / 2 + 10, (tar.pos[0] + tar.pos[1]) / 2]


def comment_label_pos(ori, tar):
    return [(ori.pos[0] + ori.pos[1]) / 2 + 10, (tar.pos[0] + tar.pos[1]) / 2 + 10]
