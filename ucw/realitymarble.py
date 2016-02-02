import os
import json

from ucw.utils import canonical_path, is_sub, class_by_name
from ucw.linkrize import linkrize

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
            target = self.adjust(target)
            return (len(self.joint_path), target)
        return (0, None)

    def adjust(self, target):
        """Adjust target before returns it"""
        return target


class NoHiddenPhantasm(Phantasm):
    """A specilized Phantasm that reveals hidden files inside it"""

    def adjust(self, target):
        (head, tail) = os.path.split(target)
        if tail.startwith('.'):
            tail = tail[1:]
        return os.path.join(head, tail)


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
        print('marble path: {}'.format(self.path))
        for ph in self.phantasms:
            print('    {} ({}), type: {}'.format(
                ph.base_path, ph.joint_path, ph.__class__))

    def collect(self, path):
        if len(self.phantasms) == 0:
            # TODO: no phantasms found
            print('no phantasm found')
            return
        if os.path.islink(path):
            # TODO: collecting a symlink
            print('collecting a symlink')
            return

        path = canonical_path(path)
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
            print('no matches found')
            return

        #print('linkrize {} to {}'.format(path, target))

        linkrize(path, target)
