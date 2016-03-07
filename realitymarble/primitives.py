import logging
import os
import shutil
import subprocess

from realitymarble import utils
from realitymarble.utils import sudolib


logger = logging.getLogger(__name__)


def exists(path):
    """check if path exists"""
    return os.path.exists(path)


def copy(src, dest):
    """copy file from source to target, w.r.t. correct mode and owner for target.
    Parent directories will be created."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    return shutil.copyfile(src, dest)


def unlink(path, force=False):
    """unlink the path, when force is True, ignore FileNotFoundError."""
    try:
        os.unlink(path)
    except FileNotFoundError:
        if not force:
            raise


def maybe_merge(src, dest):
    """try merge source to target, if src exist. Returns if it's safe to overwrite src"""
    if not os.path.exists(dest):
        logger.error('Merging to a non-existing destination: {}'.format(dest))
        return None
    if not os.path.exists(src):
        return True

    if os.path.islink(src) or not os.path.isfile(src):
        logger.error('Source is not a regular file: {}'.format(src))
        return False
    if not os.path.isfile(dest):
        logger.error('Destination is not a regular file: {}'.format(dest))
        return False

    diffcmd = ['diff', '-q', src, dest]
    try:
        res = subprocess.run(diffcmd, universal_newlines=True)
        if res.returncode == 0:
            # two files are the same
            return True
    except subprocess.SubprocessError as err:
        logger.exception(
            'Error while execution of external program: {}'.format(' '.join(diffcmd)), err)
        raise

    logger.warning('Calling external merge tool not implimented')
    return False


def edit(path):
    """use $EDITOR to edit file at path"""
    editor = os.getenv('EDITOR', 'vim')
    cmd = [editor, path]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as err:
        logger.exception(
            'Error while execution of external program: {}'.format(' '.join(cmd)), err)
        raise


def move(src, dest):
    """move file from source to target"""
    return shutil.move(src, dest)


@sudolib.retryWithSudo
def _project_unchecked(internal_path, external_path):
    """remove external_path then link external_path to internal_path"""
    finished = False
    try:
        unlink(external_path, force=True)
        os.symlink(internal_path, external_path)
        finished = True
    except Exception:
        logger.debug('Failed with exception', exc_info=True)
        raise
    finally:
        if not finished:
            # clean up
            logger.info('Roll back partially done operations')
    return finished


def _managed(base_path, external_path):
    """check if the expternal path is managed"""
    return os.path.islink(external_path) and utils.is_sub(base_path, os.readlink(external_path))


@sudolib.retryWithSudo
def _materialize_unchecked(internal_path, external_path):
    """remove external_path then copy internal_path to external_path"""
    finished = False
    try:
        unlink(external_path, force=True)
        copy(internal_path, external_path)
        finished = True
    except Exception:
        logger.debug('Failed with exception', exc_info=True)
        raise
    finally:
        if not finished:
            # clean up
            logger.info('Roll back partially done operations')
    return finished


class operations(object):
    """Operatoins"""
    def __init__(self, base_path, internal_path, external_path):
        self.base_path = base_path
        self.internal_path = internal_path
        self.external_path = external_path

    def project_unchecked(self):
        return _project_unchecked(self.internal_path, self.external_path)

    def managed(self):
        return _managed(self.base_path, self.external_path)

    def materialize_unchecked(self):
        return _materialize_unchecked(self.internal_path, self.external_path)
