import os
import sys
import subprocess
import json
import errno
import shutil
import logging
logger = logging.getLogger(__name__)

from importlib import import_module


def canonical_path(path, *paths, resolve_link=True):
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
    parent = canonical_path(parent, resolve_link=False)
    path = canonical_path(path, resolve_link=False)
    return os.path.commonprefix([parent, path]) == parent


def resolve_conflict(file, target):
    # TODO: resolve_conflict
    return False


def unlink(path, force=False):
    try:
        os.unlink(path)
    except FileNotFoundError:
        if not force:
            raise

_func_map = dict()


def sudo(funcId, *args, **kwargs):
    import __main__
    result = subprocess.run(["sudo", sys.executable, __main__.__file__, 'sudohelper',
                             funcId.__str__(), json.dumps(args)],
                            stdout=subprocess.PIPE, universal_newlines=True)
    logger.debug('Got stdout from subprocess: {}.'.format(result.stdout))
    if len(result.stdout) > 0:
        return json.loads(result.stdout)


def do(funcId, *args, **kwargs):
    func = _func_map[funcId]
    return func(*args, **kwargs)


def retryWithSudo(func):
    funcId = '.'.join([func.__module__, func.__qualname__])
    _func_map[funcId] = func
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except PermissionError:
            print("retry with sudo")
            result = sudo(funcId, *args, **kwargs)
        return result
    return wrapper


def class_by_name(name):
    parts = name.rsplit('.', 1)
    return getattr(import_module(parts[0]), parts[1])
