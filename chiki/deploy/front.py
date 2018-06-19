# coding: utf-8
from fabric.api import env, local, task, roles, run, runs_once, settings
from datetime import datetime
from .web import restart as _restart, restart_back
from .utils import execute, xput

# env.cdn_host = 'cdn.51cxin.cn'


@task
@roles('web')
def upload_etc(app='web'):
    config = '%s/etc/config' % env.path
    xput('etc/%s.py' % app, config)


@task
@roles('media')
@runs_once
def dist_media(source='../media/web/dist', target=None):
    now = datetime.now().strftime('%Y%m%d%H%M')
    target = target or '%s%s' % (env.project, now)

    local('cp -r %s /tmp/%s' % (source, target))
    run('mkdir -p /var/htdocs/www')
    local(r"""

expect -c "
spawn scp -r /tmp/%s %s@%s:/var/htdocs/www
expect {
    \"*assword\" {set timeout 500; send \"%s\r\";}
    \"yes/no\" {send \"yes\r\"; exp_continue;}
}
expect eof"

        """ % (target, env.user, env.host, env.password))


@task
@runs_once
def media(source='../media/web/dist', target=None, app='web', restart=True):
    restart = True if restart in ['True', 'true', True] else False
    now = datetime.now().strftime('%Y%m%d%H%M')
    target = target or '%s%s' % (env.project, now)

    execute(dist_media)

    for stage, e in env.envs.iteritems():
        if stage not in env.exclude_envs:
            prefix = 'SITE_STATIC_PREFIX'
            file = r'%s/etc/%s.py' % (stage, app)
            line = r'%s = \"http://%s/%s/\"' % (prefix, env.cdn_host, target)

            tpl = (
                r'[[ ! `grep %(prefix)s %(file)s` ]] && '
                r'echo "%(line)s" >> %(file)s || '
                r'sed -r -i "s#%(prefix)s.*#%(line)s#" %(file)s'
            )
            print tpl % dict(prefix=prefix, file=file, line=line)
            local(tpl % dict(prefix=prefix, file=file, line=line))

    with settings(stage='all'):
        execute(upload_etc, app)

    if restart:
        with settings(stage='all'):
            execute(_restart)
            execute(restart_back)
