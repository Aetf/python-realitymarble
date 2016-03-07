import os
import json
import sys
import logging

from realitymarble import primitives
from realitymarble import utils


logger = logging.getLogger(__name__)


DEFAULT_CONFIG = """
{
    "phantasms": [
        {
            "name": "etc",
            "type": "realitymarble.Phantasm",
            "joint_path": "/etc/"
        },
        {
            "name": "home",
            "type": "realitymarble.NoHiddenPhantasm",
            "joint_path": "/home/aetf/"
        },
        {
            "name": "scripts",
            "type": "realitymarble.ScriptsPhantasm",
            "joint_path": "/home/aetf/.local/bin"
        }
    ]
}
"""


class Phantasm(object):
    """A Phantasm is where your config files live"""

    def __init__(self, base_path, joint_path):
        self.base_path = utils.canonical_path(base_path)
        self.joint_path = utils.canonical_path(joint_path)

    def match(self, external_path):
        """Attempt to match against external_path, if succeed, returns matched length and operation object"""
        if utils.is_sub(self.joint_path, external_path):
            internal_path = os.path.join(
                self.base_path, os.path.relpath(external_path, self.joint_path))

            logger.debug('internal_path before adjust: %s', internal_path)
            internal_path = self._adjust(internal_path)
            logger.debug('internal_path after adjust: %s', internal_path)

            return (len(self.joint_path), self._create_operation(internal_path, external_path))
        return (0, None)

    def _adjust(self, internal_path):
        """Adjust target before returns it"""
        return internal_path

    def _create_operation(self, internal_path, external_path):
        return primitives.operations(self.base_path, internal_path, external_path)


class NoHiddenPhantasm(Phantasm):
    """A specilized Phantasm that reveals hidden files inside it"""

    def _adjust(self, internal_path):
        relpath = os.path.relpath(internal_path, self.base_path)
        if relpath.startswith('.'):
            relpath = relpath[1:]
        return os.path.join(self.base_path, relpath)


class ScriptsPhantasm(Phantasm):
    """A specilized Phantasm that focused on handling executable scripts"""
    pass


class RealityMarble(object):
    """docstring for RealityMarble"""
    phantasms = []

    def __init__(self, path):
        super(RealityMarble, self).__init__()
        self.path = utils.canonical_path(path)
        # load config file
        self.setup()

    def setup(self):
        # read config file inside it
        config_path = utils.canonical_path(self.path, '.realitymarble')
        if not os.path.exists(config_path):
            logger.warning(
                'Writing default configuration file: {}'.format(config_path))
            with open(config_path, "w") as fconfig:
                print(DEFAULT_CONFIG, file=fconfig)
        with open(config_path) as fconfig:
            config = json.load(fconfig)
            self._create_phantasms(config)

    def _create_phantasms(self, config):
        for ph in config['phantasms']:
            clz = utils.import_by_name(ph['type'])
            joint_path = utils.canonical_path(ph['joint_path'])
            base_path = utils.canonical_path(self.path, ph['name'])
            self.phantasms.append(clz(base_path, joint_path))

    def _match_phantasms(self, path):
        logger.debug('matching %s', path)
        matchlist = sorted([ph.match(path)
                            for ph in self.phantasms], reverse=True)
        logger.debug('matchlist is {}'.format(matchlist))
        return matchlist[0]

    def dump_config(self):
        logger.info('Reality Marble at %s', self.path)
        for ph in self.phantasms:
            logger.info('    %s (%s), type: %s', ph.base_path,
                        ph.joint_path, ph.__class__.__name__)

    def resolve_external_path(self, path):
        path = utils.canonical_path(path, resolve_link=False)
        if utils.is_sub(self.path, path):
            logger.error('Skip files inside our base')
            return None
        return path

    def collect(self, path):
        finished = False
        if len(self.phantasms) == 0:
            logger.error('No configured phantasm found.')
            return finished

        path = self.resolve_external_path(path)
        if not path:
            return finished

        if os.path.islink(path):
            logger.error('Cannot collect a symlink.')
            return finished

        (score, oper) = self._match_phantasms(path)
        if score == 0:
            logger.error('No matching phantasm found')
            return finished

        if primitives.exists(oper.internal_path):
            logger.error('Existing files found in the reality marble, try project instead: {}'.format(
                oper.internal_path))
            return finished

        logger.debug('collecting {} to {}'.format(
            oper.external_path, oper.internal_path))
        try:
            primitives.copy(oper.external_path, oper.internal_path)
            oper.project_unchecked()
            finished = True
        except Exception as err:
            logger.debug('Error while collect file: {}'.format(
                oper.external_path), exc_info=True)
        finally:
            if not finished:
                # clean up
                logger.info('roll back partially done operation for collect')
                primitives.unlink(oper.internal_path, force=True)
                utils.rmdir(os.path.dirname(oper.internal_path),
                            stop_at=self.path,
                            ignore_fail_on_non_empty=True)
        return finished

    def drop(self, path):
        finished = False
        if len(self.phantasms) == 0:
            logger.error('No configured phantasm found.')
            return finished

        path = self.resolve_external_path(path)
        if not path:
            return finished

        (score, oper) = self._match_phantasms(path)
        if score == 0:
            logger.error(
                'No matches found, this symlink is not managed by the reality marble.')
            return finished

        if not oper.managed():
            logger.error('Not a managed symlink in the reality marble: {}'.format(
                oper.external_path))
            return finished

        logger.debug('drop {} => {}'.format(
            oper.external_path, oper.internal_path))
        try:
            oper.materialize_unchecked()
            primitives.unlink(oper.internal_path)
            finished = True
        except Exception as err:
            logger.debug('Error while collect file: {}'.format(
                oper.external_path), exc_info=True)
        finally:
            if not finished:
                # clean up
                logger.info('roll back partially done operation for collect')
        return finished

    def project(self, path):
        finished = False
        if len(self.phantasms) == 0:
            logger.error('No configured phantasm found.')
            return finished

        path = self.resolve_external_path(path)
        if not path:
            return finished

        (score, oper) = self._match_phantasms(path)
        if score == 0:
            logger.error(
                'No matches found, the path trying to project to is not managed by the reality marble: {}'.format(path))
            return finished

        if not primitives.maybe_merge(oper.external_path, oper.internal_path):
            logger.error('External file exists and merge failed: {}'.format(
                oper.external_path))
            return finished

        logger.debug('project {} => {}'.format(
            oper.external_path, oper.internal_path))
        try:
            oper.project_unchecked()
            finished = True
        except Exception as err:
            logger.debug('Error while projecting file: {} => {}'.format(
                oper.external_path, oper.internal_path), exc_info=True)
        finally:
            if not finished:
                # clean up
                logger.info('roll back partially done operation for project')
        return finished

    def materialize(self, path):
        finished = False
        if len(self.phantasms) == 0:
            logger.error('No configured phantasm found.')
            return finished

        path = self.resolve_external_path(path)
        if not path:
            return finished

        (score, oper) = self._match_phantasms(path)
        if score == 0:
            logger.error(
                'No matches found, this symlink is not managed by the reality marble.')
            return finished

        if not oper.managed():
            logger.error('Symlink target is outside of the reality marble: {}'.format(
                oper.external_path))
            return finished

        logger.debug('materialize {} <= {}'.format(
            oper.external_path, oper.internal_path))
        try:
            oper.materialize_unchecked()
            finished = True
        except Exception as err:
            logger.debug('Error while materializing file: {} <= {}'.format(
                oper.external_path, oper.internal_path), exc_info=True)
        finally:
            if not finished:
                # clean up
                logger.info('roll back partially done operation for materialize')
        return finished

    def touch(self, path):
        finished = False
        if len(self.phantasms) == 0:
            logger.error('No configured phantasm found.')
            return finished

        path = self.resolve_external_path(path)
        if not path:
            return finished

        (score, oper) = self._match_phantasms(path)
        if score == 0:
            logger.error(
                'No matches found, this symlink is not managed by the reality marble.')
            return finished

        if primitives.exists(oper.internal_path):
            logger.error('Existing file found in reality marble, try project instead: {}'.format(oper.internal_path))
            return finished
        if primitives.exists(oper.external_path):
            logger.error('Existing file found, maybe you mean collect: {}'.format(oper.external_path))
            return finished


        logger.debug('touching new file {}'.format(oper.internal_path))
        try:
            primitives.edit(oper.internal_path)
            oper.project_unchecked()
            finished = True
        except Exception as err:
            logger.debug('Error while materializing file: {} <= {}'.format(
                oper.external_path, oper.internal_path), exc_info=True)
        finally:
            if not finished:
                # clean up
                logger.info('roll back partially done operation for touch')
                primitives.unlink(oper.internal_path, force=True)
                utils.rmdir(os.path.dirname(oper.internal_path),
                            stop_at=self.path, ignore_fail_on_non_empty=True)
        return finished