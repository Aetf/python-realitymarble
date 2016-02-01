import os
import shutil
from ucw.utils import canonical_path, resolve_conflict


def linkrize(path, target):
    """Make the path a symlink to customization folder"""
    if os.path.islink(path):
        return

    base = Basement(basement)
    if not base.valid:
        return

    if os.path.exists(target):
        # already exists a managed version
        print('already exists a managed version')
        if not resolve_conflict(path, target):
            return

    shutil.copy(path, target)
    os.symlink(path, target)
