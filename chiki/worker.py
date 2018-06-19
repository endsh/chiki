# coding: utf-8
import gevent
import gevent.event
import gevent.pool
import signal
import logging
import traceback

__all__ = [
    'BaseWorker', 'SimpleWorker', 'GroupWorker',
    'make_worker', 'make_group', 'worker',
    'simple_worker', 'group_worker', 'do',
    'Worker', 'GroupWorker',
]


class BaseWorker(object):

    def __init__(self, name=None, log=None, term=False):
        self.name = name if name is not None else self.__class__.__name__
        self.log = log if log is not None else logging.getLogger()
        self.event = gevent.event.Event()
        if term is True:
            gevent.signal(signal.SIGTERM, self.term)

    def wait(self, timeout=0):
        self.event.wait(timeout)

    def set(self):
        self.event.set()

    @property
    def exited(self):
        return self.event.is_set()

    def exit(self, msg=None):
        self.set()
        self.quit(msg)

    def quit(self, msg):
        self.log.info('%s - quit: %s' % (self.name, msg if msg else '...'))

    def quited(self):
        pass

    def term(self):
        self.exit('signal term.')


class SimpleWorker(BaseWorker):

    def __init__(self, name=None, timeout=0.5, log=None):
        super(SimpleWorker, self).__init__(name, log)
        self.timeout = timeout
        self.greenlet = None

    @property
    def alive(self):
        return self.greenlet and not self.greenlet.dead

    def handle(self):
        raise NotImplementedError

    def loop(self):
        while not self.exited:
            self.handle()
            self.wait(self.timeout)

    def _loop(self):
        try:
            self.loop()
        except KeyboardInterrupt:
            self.exit('KeyboardInterrupt of [%s]' % self.name)
        except Exception, e:
            self.log.warn('Exception of [%s]: %s' % (self.name, str(e)))
            self.log.debug(traceback.format_exc(limit=50))

    def join(self, timeout=0):
        if self.alive:
            self.greenlet.join(timeout)

    def kill(self, timeout=0.5):
        if self.alive:
            self.greenlet.kill(block=False, timeout=timeout)

    def quit(self, msg):
        self.log.info('%s - quiting ...' % self.name)
        self.kill()
        self.quited()

    def run(self):
        if not self.exited and not self.alive:
            self.greenlet = gevent.spawn(self._loop)

    def forever(self):
        self._loop()


class GroupWorker(SimpleWorker):

    def __init__(self, name=None, count=10, timeout=0.5, log=None):
        super(GroupWorker, self).__init__(name, timeout, log)
        self.count = count
        self.pool = gevent.pool.Pool(count)

    @property
    def free(self):
        return self.pool.free_count()

    @property
    def active(self):
        return self.count - self.free

    def spawn(self):
        for _ in xrange(min(self.free, self.count)):
            self.pool.spawn(self.handle)

    def clean(self):
        for greenlet in list(self.pool):
            if greenlet.dead:
                self.pool.discard(greenlet)

    def loop(self):
        while not self.exited:
            self.clean()
            self.spawn()
            self.wait(self.timeout)

    def quit(self, msg):
        self.log.info('%s - quiting ...' % self.name)
        self.kill()
        self.pool.kill()
        self.quited()


def make_worker(worker_class=SimpleWorker, loop=None, handle=None):

    class Worker(worker_class):

        def __init__(self, instance, *args, **kwargs):
            super(Worker, self).__init__(*args, **kwargs)
            if hasattr(instance, 'wait'):
                self.wait = instance.wait
            if hasattr(instance, 'exit'):
                self.exit = instance.exit
            if hasattr(instance, 'exited'):
                self.__dict__['exited'] = property(lambda: instance.exited)

    if loop is not None:
        Worker.loop = loop
    if handle is not None:
        Worker.handle = handle

    return Worker


def make_group(loop=None, handle=None):
    return make_worker(GroupWorker, loop, handle)


def worker(instance, worker_class=SimpleWorker, loop=None,
        handle=None, *args, **kwargs):
    _worker = make_worker(worker_class, loop, handle)
    return _worker(instance, *args, **kwargs)


def simple_worker(instance, loop=None, handle=None, *args, **kwargs):
    return worker(instance, loop=loop, handle=handle, *args, **kwargs)


def group_worker(instance, loop=None, handle=None, *args, **kwargs):
    return worker(instance, worker_class=GroupWorker,
        loop=loop, handle=handle, *args, **kwargs)


def do(tasks, handle, count=10, timeout=0.1):
    results = []

    class TaskWorker(GroupWorker):

        def handle(self):
            while tasks:
                task = tasks.pop()
                results.append((task, handle(task)))

        @property
        def exited(self):
            return not tasks

    TaskWorker().forever()

    return results


Worker = make_worker()
Group = make_group()
