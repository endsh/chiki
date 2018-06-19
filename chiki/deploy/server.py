# coding: utf-8
from fabric.api import cd, env, settings
from .utils import FabricException, xrun, roles, task


def _start(*args):
    for arg in args:
        with cd(env.path):
            xrun('uwsgi --ini %s/etc/uwsgi/%s.ini' % (env.path, arg),
                 envs='LOGGER_DEBUG=True')


def _start_back(*args):
    for arg in args:
        with cd(env.path):
            xrun('uwsgi --ini %s/etc/uwsgi/%s.ini' % (
                env.path, arg), envs='CHIKI_BACK=true')


def _stop(*args):
    for arg in args:
        with settings(abort_exception=FabricException):
            try:
                xrun('uwsgi --stop %s/run/%s.pid' % (env.path, arg))
            except FabricException as e:
                print str(e)


@roles('web')
@task
def start():
    _start(*env.apps)


@roles('web')
@task
def stop():
    _stop(*env.apps)


@roles('web')
@task
def restart():
    stop()
    start()


@roles('web')
@task
def start_back():
    _start_back(*['%s.back' % x for x in env.apps])


@roles('web')
@task
def stop_back():
    _stop(*['%s.back' % x for x in env.apps])


@roles('web')
@task
def restart_back():
    stop_back()
    start_back()
