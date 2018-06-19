# coding: utf-8
import os
from fabric.api import cd, env, run, roles, task, lcd
from fabric.api import settings, local, runs_once, put
from fabric.contrib.files import exists, append
from .nginx import nginx
from .server import restart, restart_back
from .utils import execute, xrun, xput, scp


@task
def all():
    execute(init)
    execute(create_env)
    execute(pip)
    execute(deploy)
    execute(nginx)


def build():
    run('apt-get update')
    run(
        'apt-get install -y vim software-properties-common'
        ' python-setuptools nginx --force-yes'
        ' libmysqlclient-dev git gcc g++ unzip'
        ' python-virtualenv python-dev subversion curl'
        ' libxml2-dev libxslt1-dev libfreetype6-dev'
        ' libjpeg62 libpng3 libjpeg-dev libpng12-dev'
        ' libffi-dev libssl-dev expect sshpass'
    )
    run('easy_install pip supervisor')
    run('pip install virtualenvwrapper')

    run('sed -i "s/#   StrictHostKeyChecking ask/'
        'StrictHostKeyChecking no/g" /etc/ssh/ssh_config')


def create_user(name):
    if not exists('/home/%s' % name):
        run('echo "\n\n\n\n\nY\n" | adduser --disabled-password -q %s' % name)
        run('usermod -p $(openssl passwd -1 %s) %s' % (
            env.user_password, name))


@roles('web')
@task
def remove_user(name=None):
    if not name:
        name = env.user
    with settings(user='root', password=env.sudo_password):
        run('killall -u %s' % name)
        run('userdel %s' % name)
        run('rm -rf /home/%s' % name)


@roles('web')
@task
def init():
    user = env.user
    with settings(user='root', password=env.sudo_password):
        build()
        create_user(user)


@roles('web')
@task
def create_env():
    run('mkdir -p /home/%s/.ssh' % env.user)
    rsa = '/home/%s/.ssh/id_rsa_%s' % (env.user, env.project)
    xput('files/id_rsa', rsa)
    run('chmod 600 %s' % rsa)
    append('~/.ssh/config', 'IdentityFile %s' % rsa)

    profile = '~/.bash_profile_%s' % env.project
    xput('files/bash_profile', profile)
    append('~/.bashrc', 'source %s' % profile)

    run('mkdir -p ~/.pip')
    xput('files/pip.conf', '~/.pip/pip.conf')
    if not exists('/home/%s/.virtualenvs/%s' % (env.user, env.project)):
        cmd = 'source /usr/local/bin/virtualenvwrapper.sh && mkvirtualenv %s'
        run(cmd % env.project)

    for path in [env.path, env.src, env.dist]:
        run('mkdir -p %s' % path)

    dirnames = ['data', 'etc/config', 'etc/uwsgi', 'run', 'logs']
    for dirname in dirnames:
        run('mkdir -p %s/%s' % (env.path, dirname))

    config = '%s/etc/config' % env.path
    uwsgi = '%s/etc/uwsgi' % env.path
    xput('etc/base.py', config)
    for app in env.apps:
        xput('etc/%s.py' % app, config)
        xput('uwsgi/%s.ini' % app, uwsgi)
        xput('uwsgi/%s.back.ini' % app, uwsgi)


@roles('web')
@task
def pip(file='../requirements/prod.txt'):
    put(file, os.path.join(env.path, 'requirements.txt'))
    with cd(env.path):
        # xrun('pip install -r setuptools==35.0.2')
        xrun('pip install -r requirements.txt')


@roles('repo')
@task
def clone(name, folder, repo=None, branch=None, copy=False,
          media='media/web/dist data'):
    if exists(folder + '/.git'):
        run('cd %s && git stash && git pull' % folder)
    else:
        run('git clone %s %s' % (repo or env.repo, folder))

    if branch:
        run('cd %s && git checkout %s' % (folder, branch))

    if exists(folder + '/setup.py'):
        with cd(folder):
            run('rm -rf dist `python setup.py --fullname`')
            run('python setup.py sdist')
            run('mv dist/`python setup.py --fullname`'
                '.tar.gz %s.tar.gz' % name)

    if copy:
        with cd(folder):
            run('tar -zcvf %s.media.tar.gz %s' % (name, media))


@roles('repo')
@task
def srepo(folder, items):
    with cd(folder):
        for key, item in items:
            put(key, item)


@roles('web')
@task
def setup(name, folder, copy=False, is_scp=True):
    source = os.path.join(folder, '%s.tar.gz' % name)
    target = os.path.join(env.dist, '%s.tar.gz' % name)
    if is_scp:
        scp(source, target, env.repo_host, getattr(env, 'repo_password', ''))
    else:
        put(source, target)

    with cd(env.dist):
        run('tar -zxvf %s.tar.gz' % name)
        run("mv `gzip -dc %s.tar.gz | tar tvf -| awk '{print $6}' "
            "| awk -F '/' '{print $1}'|uniq` %s" % (name, name))
        with cd(name):
            xrun('python setup.py install')
        if exists(name):
            run('rm -r %s' % name)

    if copy:
        source = os.path.join(folder, '%s.media.tar.gz' % name)
        target = os.path.join(env.dist, '%s.media.tar.gz' % name)
        if is_scp:
            scp(source, target, env.repo_host, getattr(
                env, 'repo_password', ''))
        else:
            put(source, target)
        with cd(env.path):
            run('tar -zxvf %s' % target)


@task
def clone2setup(name, folder, repo=None, branch=None, copy=False,
                media='media/web/dist data'):
    execute(clone, name, folder, repo, branch, copy=copy, media=media)
    execute(setup, name, folder, copy=copy)


@task
def clone4github():
    repos = {
        'chiki': {
            'repo': 'https://github.com/endsh/chiki.git',
            'branch': 'old',
        },
        'simi': 'git@gitlab.com:xiaoku/simi.git',
        'flask-admin': "https://github.com/flask-admin/flask-admin.git",
    }
    for name, repo in repos.iteritems():
        folder = os.path.join(env.src, name)
        if type(repo) == dict:
            clone2setup(name, folder, repo['repo'], repo['branch'])
        else:
            clone2setup(name, folder, repo)


@task
def sdist(copy=False, media='media/web/dist'):
    copy = True if copy in ['True', 'true', True] else False
    with lcd('../'):
        local('python setup.py sdist')
        local('mv dist/`python setup.py --fullname`'
              '.tar.gz dist/%s.tar.gz' % env.project)

        if copy:
            local('tar -zcvf dist/%s.media.tar.gz %s' % (
                env.project, media))
            execute(srepo, env.dist, [
                ('dist/%s.tar.gz' % env.project,
                 '%s.tar.gz' % env.project),
                ('dist/%s.media.tar.gz' % env.project,
                 '%s.media.tar.gz' % env.project),
            ])
        else:
            execute(srepo, env.dist, [
                ('dist/%s.tar.gz' % env.project,
                 '%s.tar.gz' % env.project),
            ])

    execute(setup, env.project, env.dist, copy=copy)


@task
def simi():
    folder = os.environ.get('SIMI_DIR')
    with lcd(folder):
        local('python setup.py sdist')
        local('mv dist/`python setup.py --fullname`.tar.gz dist/simi.tar.gz')

        execute(srepo, env.dist, [
            ('dist/simi.tar.gz', 'simi.tar.gz'),
        ])

    execute(setup, 'simi', env.dist)


@task
def chiki():
    folder = os.environ.get('CHIKI_DIR')
    with lcd(folder):
        local('python setup.py sdist')
        local('mv dist/`python setup.py --fullname`.tar.gz dist/chiki.tar.gz')

        execute(srepo, env.dist, [
            ('dist/chiki.tar.gz', 'chiki.tar.gz'),
        ])

    execute(setup, 'chiki', env.dist)


@task
def update(copy=False, media='media/web/dist data'):
    copy = True if copy in ['True', 'true', True] else False
    clone2setup(env.project, os.path.join(env.src, env.project), copy=copy)


@task
def deploy():
    execute(update)
    execute(clone4github)


@task
@runs_once
def commit(msg='auto commit', project=None):
    folder = '..'
    branch = 'master'
    if project:
        if project == 'simi':
            folder = os.environ.get('SIMI_DIR')
        elif project == 'chiki':
            folder = os.environ.get('CHIKI_DIR')
            branch = 'old'

    with lcd(folder):
        local('git add --all .')
        local('git commit -m "%s"' % msg)
        local('git push -u origin %s' % branch)


@task
def sync(msg='auto commit'):
    commit(msg)
    execute(update)


@task
def up(msg='auto commit'):
    sync(msg)
    execute(restart)


@task
def upx(msg='auto commit'):
    sync(msg)
    execute(restart)
    execute(restart_back)
