# coding: utf-8
from fabric.api import cd, env, local, run, sudo
from fabric.api import execute, hosts, lcd, put, settings
from fabric.contrib.files import exists, append

env.user = 'simple@chiki.org'
env.password = ''
ROOT = 'root@chiki.org'
PROJECT_NAME = 'simple'
SOURCE_FOLDER = '/home/%s/%s' % ('simple', PROJECT_NAME)
REPO_URL = 'git@gitlab.com:tinysh/simple.git'


class FabricException(Exception):
    pass


def all():
    execute(init)
    execute(deploy, True)
    execute(nginx)


@hosts(ROOT)
def init():
    build()
    user('simple')


def build():
    sudo('apt-get update')
    sudo('apt-get install -y vim software-properties-common')
    sudo('apt-get install -y python-setuptools')
    sudo('easy_install pip supervisor')
    sudo('apt-get install -y python-virtualenv')
    sudo('apt-get install -y python-dev subversion curl')
    sudo('apt-get install -y libmysqlclient-dev git gcc g++ unzip')
    sudo('apt-get install -y nginx mongodb')
    sudo('pip install virtualenvwrapper')


def user(name):
    if not exists('/home/%s' % name):
        sudo('adduser %s' % name)
    run('mkdir -p /home/%s/.ssh' % name)
    put('files/id_rsa', '/home/%s/.ssh' % name)
    run('chmod 600 /home/%s/.ssh/id_rsa' % name)
    run('chown -R %s:%s /home/%s' % (name, name, name))


@hosts(env.user)
def deploy(extends=False):
    clone_code()
    mkvir(extends=extends)
    mkenv()


@hosts(env.user)
def update():
    clone_code()


def clone_code(source_folder=SOURCE_FOLDER):
    if exists(source_folder + '/.git'):
        run('cd %s && git stash && git pull' % source_folder)
    else:
        run('git clone %s %s' % (REPO_URL, source_folder))


def clone2setup(name, git):
    if not exists(name):
        run('git clone %s %s' % (git, name))
    else:
        run('cd %s && git stash && git pull' % name)
    with cd(name):
        run('~/.virtualenvs/%s/bin/python setup.py install' % PROJECT_NAME)


def mkvir(name=PROJECT_NAME, source_folder=SOURCE_FOLDER, extends=False):
    run('source /usr/local/bin/virtualenvwrapper.sh && mkvirtualenv %s' % name)
    run('~/.virtualenvs/%s/bin/pip install -r %s/requirements.txt' % (name, source_folder))

    if extends:
        mkextends()


def mkextends():
    run('mkdir -p ~/git')
    gits = {
       'chiki': "https://github.com/endsh/chiki.git",
       'flask-admin': "https://github.com/flask-admin/flask-admin.git",
    }
    with cd('~/git'):
        for name, git in gits.iteritems():
            clone2setup(name, git)


def mkenv(source_folder=SOURCE_FOLDER):
    put('files/bash_profile', '~/.bash_profile')
    append('~/.bashrc' , 'source ~/.bash_profile')
    for dirname in ['etc', 'run', 'logs']:
        run('mkdir -p %s/%s' % (source_folder, dirname))

    etc = '%s/%s' % (source_folder, 'etc')
    put('etc/admin.cfg', etc)
    put('etc/admin.ini', etc)
    put('etc/admin.back.ini', etc)
    put('etc/api.cfg', etc)
    put('etc/api.ini', etc)
    put('etc/api.back.ini', etc)
    put('etc/web.cfg', etc)
    put('etc/web.ini', etc)
    put('etc/web.back.ini', etc)


def up(msg='auto commit'):
    sync(msg)
    execute(restart)


def sync(msg='auto commit'):
    commit(msg)
    execute(update)


def commit(msg='auto commit'):   
    local('git add --all ..')
    local('git commit -m "%s"' % msg)
    local('git push -u origin master')


@hosts(env.user)
def pip():
    run('pip install -r %s/requirements.txt' % SOURCE_FOLDER)


def spip():
    sync()
    execute(pip)


@hosts(ROOT)
def nginx():
    nginx_config()
    nginx_reload()


def nginx_config():
    put('nginx/simple.nginx.conf', '/etc/nginx/sites-enabled')


def nginx_reload():
    run('service nginx reload')


def _start(*args):
    for arg in args:
        run('~/.virtualenvs/%s/bin/uwsgi --ini %s/etc/%s.ini' % (
            PROJECT_NAME, SOURCE_FOLDER, arg))


def _start_back(*args):
    for arg in args:
        run('CHIKI_BACK=true ~/.virtualenvs/%s/bin/uwsgi --ini %s/etc/%s.ini' % (
            PROJECT_NAME, SOURCE_FOLDER, arg))


def _stop(*args):
    for arg in args:
        with settings(abort_exception=FabricException):
            try:
                run('~/.virtualenvs/%s/bin/uwsgi --stop %s/run/%s.pid' % (
                        PROJECT_NAME, SOURCE_FOLDER, arg))
            except FabricException, e:
                print str(e)


@hosts(env.user)
def start():
    _start('admin', 'api', 'web')


@hosts(env.user)
def stop():
    _stop('admin', 'api', 'web')


@hosts(env.user)
def restart():
    stop()
    start()


@hosts(env.user)
def start_back():
    _start_back('admin.back', 'api.back', 'web.back')


@hosts(env.user)
def stop_back():
    _stop('admin.back', 'api.back', 'web.back')


@hosts(env.user)
def restart_back():
    stop_back()
    start_back()


def setup_ssh():
    local('cp files/id_rsa ~/.ssh/id_%s' % PROJECT_NAME)
    local('cp files/id_rsa.pub ~/.ssh/id_%s.pub' % PROJECT_NAME)
    local('chmod -R 0600 ~/.ssh/id_%s*' % PROJECT_NAME)