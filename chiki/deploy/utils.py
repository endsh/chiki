# coding: utf-8
import os
import fabric
from fabric.api import cd, env, run, local, roles, task
from fabric.api import put, settings, execute as _execute


class FabricException(Exception):
    pass


def xput(source, target, sudo=False):
    if not source.startswith('/'):
        filename = '%s/%s' % (env.stage, source)
        if os.path.isfile(filename):
            source = filename
        else:
            source = 'common/%s' % source
    return put(source, target, use_sudo=sudo)


def xrun(cmd, envs=''):
    return run('%s ~/.virtualenvs/%s/bin/%s' % (envs, env.project, cmd))


def scp(source, target, host, password=None):
    run("sshpass -p %s scp %s:%s %s" % (
        password or env.password, host, source, target))


def execute(task, *args, **kwargs):
    if 'exclude_envs' not in env:
        env.exclude_envs = ['test']

    if task not in ['stage', 's']:
        if env.stage == 'all':
            for stage, e in env.envs.iteritems():
                if stage not in env.exclude_envs:
                    with settings(stage=stage, **e):
                        _execute(task, *args, **kwargs)
            return
        elif env.stage in env.envs:
            with settings(stage=env.stage, **env.envs[env.stage]):
                return _execute(task, *args, **kwargs)
    return _execute(task, *args, **kwargs)


fabric.main.execute = execute
fabric.api.execute = execute


@task(alias='s')
def stage(stage='all'):
    env.stage = stage


@roles('web', 'db', 'front', 'puppet')
@task
def ssh_config():
    with settings(user='root', password=env.sudo_password):
        with cd('/etc/ssh'):
            run('sed -i "s/#ClientAliveInterval 0/ClientAliveInterval 60/g"'
                ' sshd_config')
            run('sed -i "s/#ClientAliveCountMax 3/ClientAliveCountMax 3/g"'
                ' sshd_config')
            run('service ssh reload')


@roles('web')
@task
def tail_log(name='uwsgi.admin', line=100):
    run('tail -n %d %s/logs/%s.log' % (int(line), env.path, name))


@roles('web')
@task
def git_config():
    run('git config --global user.email "tiger@qq.com"')
    run('git config --global user.name "tiger"')


@roles('main')
@task
def crontab():
    filename = os.path.join(env.path, 'etc/cron.conf')
    xput('files/cron.conf', filename)

    run(r'crontab -l | sed "s#no crontab for %(user)s##g"'
        r' | sed ":a;N;s#\n#@@#g;ta"'
        r' | sed "s=## %(branch)s start.*## %(branch)s end==g"'
        r' | sed "s#@@#\n#g" > ~/cron.conf' % dict(
            user=env.user,
            branch=env.branch,
            filename=filename,
        ))

    run('echo "\n## %s start" >> ~/cron.conf' % env.branch)
    run('cat %s >> ~/cron.conf' % filename)
    run('echo "## %s end\n" >> ~/cron.conf' % env.branch)
    run('cat ~/cron.conf')
    run('crontab ~/cron.conf')


@roles('main')
@task
def clear_crontab():
    run('echo "# clear crontab\n" > ~/cron.conf')
    run('crontab ~/cron.conf')


@roles('main')
@task
def service(command):
    with cd(env.path):
        xrun("%s service %s" % (env.project, command))


@roles('main')
@task
def start_service(name):
    with cd(env.path):
        with settings(abort_exception=FabricException):
            try:
                run('kill -s 15 `cat %s/run/%s.pid`' % (env.path, name))
            except FabricException:
                pass
            run('$(nohup ~/.virtualenvs/%(project)s/bin/%(project)s service'
                ' %(name)s >> %(path)s/logs/%(name)s.log 2>&1 &) && sleep 3'
                % dict(
                    project=env.project,
                    name=name,
                    path=env.path,
                ))


@roles('main')
@task
def stop_service(name):
    with cd(env.path):
        with settings(abort_exception=FabricException):
            try:
                run('kill -s 15 `cat %s/run/%s.pid`' % (env.path, name))
            except FabricException:
                pass


@task
def cmd(text):
    run(text)


@task
def ssh(host=None, user=None):
    if not host:
        host = env.roledefs['main'][0]

    if not user:
        user = env.user

    if '@' in host:
        local('ssh %s' % host)
    else:
        local('ssh %s@%s' % (user, host))
