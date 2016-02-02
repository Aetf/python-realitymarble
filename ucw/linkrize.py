import os
import sys
import errno
import shutil
from ucw.utils import canonical_path, resolve_conflict, sudo, unlink


def linkrize(path, target):
    """Make the path a symlink to customization folder"""
    finished = False
    if os.path.islink(path):
        # TODO: handle already a link
        print('already a link', file=sys.stderr)
        return finished

    print('target is {}'.format(target), file=sys.stderr)
    if os.path.exists(target):
        # TODO: already exists a managed version
        print('already exists a managed version', file=sys.stderr)
        if not resolve_conflict(path, target):
            return finished

    try:
        shutil.move(path, target)
        os.symlink(target, path)
        finished = True
    except PermissionError as err:
        # clean up
        print('clean up before sudo', file=sys.stderr)
        unlink(target, force=True)
        # redo with sudo
        finished = sudo(os.symlink, path, target)
    finally:
        if not finished:
            # clean up
            print('clean up', file=sys.stderr)
            unlink(target, force=True)
    return finished
