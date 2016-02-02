import os
import sys
import subprocess
import json
import errno
import shutil
from importlib import import_module
import __main__


def canonical_path(path, *paths):
    path = os.path.join(path, *paths)
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
    # TODO: resolve_conflict
    return False


def unlink(path, force=False):
    try:
        os.unlink(path)
    except FileNotFoundError:
        if not force:
            raise


def sudo(func, *args, **kwargs):
    result = subprocess.run(["sudo", sys.executable, __main__.__file__, 'sudohelper',
                             'ucw.linkrize.linkrize'] + [json.dumps(args)],
                            stdout=subprocess.PIPE, universal_newlines=True)
    print('Got stdout from subprocess: {}.'.format(result.stdout))
    if len(result.stdout) > 0:
	    return json.loads(result.stdout)


def class_by_name(name):
    parts = name.rsplit('.', 1)
    return getattr(import_module(parts[0]), parts[1])
