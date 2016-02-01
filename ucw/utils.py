import os


def canonical_path(path):
    path = os.path.expanduser(path)
    path = os.path.realpath(path)
    if os.path.isdir(path):
        path = os.path.join(path, '')
    return path


def is_sub(parent, path):
    parent = canonical_path(parent)
    path = canonical_path(path)
    return os.path.commonprefix([parent, path]) == parent


def resolve_conflict(file, target):
    return False

