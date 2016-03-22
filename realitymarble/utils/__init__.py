import errno
import importlib
import logging
import os
import shutil


logger = logging.getLogger(__name__)


def canonical_path(path, *paths, **kwargs):
    """Canonicalize path, expand user and convert to abspath or realpath if resolve_link set to True. Paths to a directory are appended a slash."""
    resolve_link = kwargs.pop('resolve_link', True)
    path = os.path.join(path, *paths)
    path = os.path.expanduser(path)
    if resolve_link:
        path = os.path.realpath(path)
    else:
        path = os.path.abspath(path)
    if os.path.isdir(path):
        path = os.path.join(path, '')
    return path


def is_sub(parent, path):
    """if path is considered inside parent path"""
    parent = canonical_path(parent, resolve_link=False)
    path = canonical_path(path, resolve_link=False)
    return os.path.commonprefix([parent, path]) == parent


def rmdir(path, stop_at='', ignore_fail_on_non_empty=False, continue_on_parent=True):
    """remove empty directories"""
    if not os.path.isdir(path):
        raise NotADirectoryError

    if len(stop_at) != 0 and not is_sub(stop_at, path):
        raise ValueError("stop_at must be a parent of path if it's not empty")

    while True:
        try:
            os.rmdir(path)
        except OSError as err:
            if err.errno == errno.ENOTEMPTY and ignore_fail_on_non_empty:
                break
            raise
        if not continue_on_parent:
            break
        path = os.path.dirname(path)
        if len(stop_at) != 0 and not is_sub(stop_at, path):
            break


def import_by_name(name):
    parts = name.rsplit('.', 1)
    return getattr(importlib.import_module(parts[0]), parts[1])


def resolve_conflict(file, target):
    # TODO: resolve_conflict
    return False
