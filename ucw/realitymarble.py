import os

from ucw.utils import canonical_path, is_sub
from ucw.linkrize import linkrize


class RealityMarble(object):
    """docstring for RealityMarble"""

    def __init__(self, path):
        super(RealityMarble, self).__init__()
        self.path = canonical_path(path)
        self.etc = canonical_path(os.path.join(self.path, 'etc'))
        self.home = canonical_path(os.path.join(self.path, 'home'))
        self.scripts = canonical_path(os.path.join(self.path, 'scripts'))
        # verify paths
        if not self.verify():
            self.setup()


    def verify(self):
        valid = True
        for p in self.path, self.etc, self.home, self.scripts:
            valid = valid and os.path.isdir(p)
        return valid

    def setup(self):
        #TODO setup
        pass

    def contains(self, path):
        return is_sub(self.path, path)

    def collect(self, path):
        if os.path.islink(path):
            return

        home = canonical_path('~/')
        etc = canonical_path('/etc/')
        if self.contains(path):
            # skip files inside our base
            print('skip files inside our base')
            return
        elif is_sub(home, path):
            # link to home
            print('link to home')
            target = os.path.join(base.home, os.path.relpath(path, home))
            (head, tail) = os.path.split(target)
            if tail.startwith('.'):
                tail = tail[1:]
            target = os.path.join(head, tail)
        elif is_sub(etc, path):
            # link to etc
            print('link to etc')
            target = os.path.join(base.etc, os.path.relpath(path, etc))
        else:
            # don't touch files outside
            print("don't touch files outside")
            return
        linkrize(path, target)
