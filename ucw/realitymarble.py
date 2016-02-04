import os
import json
import sys
import logging
logger = logging.getLogger(__name__)

from ucw.utils import canonical_path, is_sub, class_by_name
from ucw.linkrize import linkrize, unlinkrize

DEFAULT_CONFIG = """
{
    "phantasms": [
        {
            "name": "etc",
            "type": "Phantasm",
            "joint_path": "/etc/"
        },
        {
            "name": "home",
            "type": "NoHiddenPhantasm",
            "joint_path": "/home/aetf/"
        },
        {
            "name": "scripts",
            "type": "ScriptsPhantasm",
            "joint_path": "/home/aetf/.local/bin"
        }
    ]
}
"""


class Phantasm(object):
    """A Phantasm is where your config files live"""

    def __init__(self, base_path, joint_path):
        self.base_path = canonical_path(base_path)
        self.joint_path = canonical_path(joint_path)

    def match(self, path):
        """Attempt to match against path, if succeed, returns matched target and matched length"""
        if is_sub(self.joint_path, path):
            target = os.path.join(
                self.base_path, os.path.relpath(path, self.joint_path))

            logger.debug('target before adjust: %s', target)
            target = self._adjust(target)
            logger.debug('target after adjust: %s', target)

            return (len(self.joint_path), target)
        return (0, None)

    def _adjust(self, target):
        """Adjust target before returns it"""
        return target


class NoHiddenPhantasm(Phantasm):
    """A specilized Phantasm that reveals hidden files inside it"""

    def _adjust(self, target):
        relpath = os.path.relpath(target, self.base_path)
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
        self.path = canonical_path(path)
        # verify paths
        self.setup()

    def setup(self):
        # read config file inside it
        config_path = canonical_path(self.path, '.realitymarble')
        if not os.path.exists(config_path):
            # TODO: config file not found, use default
            with open(config_path, "w") as fconfig:
                print(DEFAULT_CONFIG, file=fconfig)
        with open(config_path) as fconfig:
            self.create_phantasms(fconfig)

    def create_phantasms(self, fconfig):
        config = json.load(fconfig)
        for ph in config['phantasms']:
            clz = class_by_name(ph['type'])
            joint_path = canonical_path(ph['joint_path'])
            base_path = canonical_path(self.path, ph['name'])
            self.phantasms.append(clz(base_path, joint_path))

    def dump_config(self):
        logger.info('Reality Marble at %s', self.path)
        for ph in self.phantasms:
            logger.info('    %s (%s), type: %s', ph.base_path,
                        ph.joint_path, ph.__class__.__name__)

    def collect(self, path):
        if len(self.phantasms) == 0:
            logger.error('no configured phantasm found.')
            return
        if os.path.islink(path):
            logger.error('can not collect a symlink.')
            return

        path = canonical_path(path)
        if is_sub(self.path, path):
            logger.error('skip files inside our base')
            return

        logger.debug('matching %s', path)

        matchlist = sorted([ph.match(path)
                            for ph in self.phantasms], reverse=True)
        logger.debug('matchlist is {}'.format(matchlist))
        (score, target) = matchlist[0]
        if score == 0:
            # TODO: no matches found
            logger.error('no matching phantasm found')
            return

        logger.debug('linkrize {} to {}'.format(path, target))
        linkrize(path, target)

    def drop(self, path):
        if len(self.phantasms) == 0:
            logger.error('no configured phantasm found.')
            return
        if not os.path.islink(path):
            logger.error('can not drop a non-symlink.')
            return

        path = canonical_path(path, resolve_link=False)
        logger.debug('canonicalized path: {}'.format(path))
        if is_sub(self.path, path):
            # TODO: skip files inside our base
            print('skip files inside our base')
            return

        print('matching {}'.format(path))
        matchlist = sorted([ph.match(path)
                            for ph in self.phantasms], reverse=True)
        print('matchlist is {}'.format(matchlist))
        (score, target) = matchlist[0]
        if score == 0:
            # TODO: no matches found
            print('no matches found, this symlink is not managed by the reality marble.')
            return

        logger.debug('unlinkrize {}'.format(path))
        unlinkrize(path)
