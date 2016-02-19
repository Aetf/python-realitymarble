import json
import logging
import subprocess
import sys

from realitymarble.utils import canonical_path, import_by_name


logger = logging.getLogger(__name__)


def sudo(funcDesc, *args, **kwargs):
    """execute a function using root user privilege, returns whatever func returned."""
    msg = {
        'args': args,
        'kwargs': kwargs,
        'func': funcDesc
    }
    result = subprocess.run(['sudo', sys.executable,
                             canonical_path(__file__), json.dumps(msg)],
                            stdout=subprocess.PIPE, universal_newlines=True)
    logger.debug('Got stdout from subprocess: {}.'.format(result.stdout))
    if len(result.stdout) > 0:
        return json.loads(result.stdout)


def retryWithSudo(func):
    funcDesc = '.'.join([func.__module__, func.__qualname__])

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except PermissionError:
            logger.info("retry with sudo")
            result = sudo(funcDesc, *args, **kwargs)
        return result
    return wrapper


if __name__ == '__main__':
    import importlib

    def do(msg):
        """decode msg passed in by sudo and actually execute the func"""
        func = import_by_name(msg['func'])
        return func(*msg['args'], **msg['kwargs'])

    try:
        msg = json.loads(sys.argv[1])
        print(json.dumps(do(msg)))
    except:
        logger.exception("Exception in subprocess")
