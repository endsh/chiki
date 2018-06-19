# coding: utf-8
import os
import fcntl
import inspect
import signal
import time
import traceback
from functools import wraps
from flask import current_app
from chiki.contrib.common import TraceLog

cmds = dict()


def service(cmd=None, model='simple'):
    def add(func):
        c = cmd or func.__name__
        if cmd not in cmds:
            cmds[c] = dict()
        cmds[c][model] = func
        return func
    return add


def run(cmd, model='simple'):
    if cmd in cmds:
        func = cmds[cmd].get(model, cmds[cmd].get('simple'))
        if func:
            if inspect.getargspec(func)[0]:
                func(model)
            else:
                func()
            return True
    return False


def single(filename):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pid = str(os.getpid())
            pidfile = open(filename, 'a+')
            try:
                # 创建一个排他锁,并且所被锁住其他进程不会阻塞
                fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return

            pidfile.seek(0)
            pidfile.truncate()
            pidfile.write(pid)
            pidfile.flush()
            pidfile.seek(0)

            res = func(*args, **kwargs)

            try:
                pidfile.close()
            except IOError, err:
                if err.errno != 9:
                    return
            os.remove(filename)
            return res
        return wrapper
    return decorator


def loop(name, sleep=5):
    """ 循环服务 """

    exit = []

    def signal_term(a, b):
        exit.append(True)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            folder = current_app.config.get('RUN_FOLDER', '')
            filename = os.path.join(folder, '%s.pid' % name)
            with open(filename, 'w+') as fd:
                fd.write(str(os.getpid()))

            if current_app.debug:
                print 'start service with process:', os.getpid()

            signal.signal(signal.SIGTERM, signal_term)

            while not exit:
                try:
                    func()

                    i = 0
                    while i < sleep * 10:
                        i += 1
                        time.sleep(0.1)
                except KeyboardInterrupt as e:
                    break
                except Exception:
                    traceback.print_exc()
                    TraceLog(
                        key='service-%s' % name,
                        value=traceback.format_exc(),
                    ).save()

            os.remove(filename)
        return wrapper
    return decorator
