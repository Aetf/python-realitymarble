import os
import sys
import errno
import shutil
import logging
logger = logging.getLogger(__name__)

from realitymarble.utils import canonical_path, unlink, rmdir, resolve_conflict
from realitymarble.utils import sudolib


@sudolib.retryWithSudo
def unlinkrize(path):
    finished = False
    """Replace a symlink at path with its target"""
    if not os.path.islink(path):
        logger.error('%s is not a symlink', path)
        return finished

    target = os.readlink(path)
    if not os.path.isabs(target):
        target = os.path.join(os.path.dirname(path), target)
        target = os.path.abspath(target)

        logger.debug('unlinkrize %s -> %s', path, target)
    try:
        os.unlink(path)
        shutil.move(target, path)
        finished = True
    finally:
        if not finished:
            # clean up
            logger.info('roll back partially done operation for unlinkrize')


@sudolib.retryWithSudo
def linkrize(path, target):
    """Make the path a symlink to customization folder"""
    finished = False
    if os.path.islink(path):
        # TODO: handle already a link
        logger.error('%s is already a symlink', path)
        return finished

    logger.debug('linkrize %s to target %s', path, target)

    if os.path.exists(target):
        logger.warning('there already exists a managed file version', path)
        if not resolve_conflict(path, target):
            return finished

    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(path, target)
        unlink(path)
        os.symlink(target, path)
        finished = True
    except Exception as err:
        logger.debug('The following exception raised when linkrize:', exc_info=True)
        raise
    finally:
        if not finished:
            # clean up
            logger.info('roll back partially done operation for linkrize')
            unlink(target, force=True)
            rmdir(os.path.dirname(target), ignore_fail_on_non_empty=True)
    return finished
