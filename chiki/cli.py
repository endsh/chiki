# coding: utf-8
import re
import os
import sys
import inspect
from datetime import datetime
from cookiecutter.main import cookiecutter
from flask import Flask
from flask.ext.script import Manager, Command, Shell
from chiki.base import db
from chiki.app import apps
from chiki.contrib.users import um
from chiki.service import run as run_service

commands = dict()


def command(cmd=None):
    def wrapper(func):
        global commands
        commands[cmd or func.__name__] = func
        return func
    return wrapper


def search_item(path, items):
    for name in os.listdir(path):
        subpath = os.path.join(path, name)
        if os.path.isdir(subpath):
            search_item(subpath, items)
        elif subpath.rsplit('.', 1)[-1] in ['py', 'htm', 'html']:
            with open(subpath) as fd:
                subs = re.findall('(Item\.(?!set).+?\((.|\n)+?\))', fd.read())
                items += [re.sub(',\n +', ', ', sub[0]) for sub in subs]


@command('item')
def create_item():
    items = []
    name = os.popen('python setup.py --name').read()[:-1]
    search_item(name, items)
    search_item('templates', items)

    res = dict()
    for item in items:
        if "%" in item:
            item = "# " + item
        match = re.search(r'\([\'"](.*?)[\'"]', item)
        if match:
            res[match.group(1)] = item
        else:
            res[item] = item

    items = [x for _, x in sorted(res.iteritems(), key=lambda m: m[0])]

    path = os.path.join(name, 'services/init.py')
    content = """# coding: utf-8
from chiki.admin.common import documents
from chiki.contrib.common import Item


def init_items():
    pass


def init():
    pass


def clear_db():
    for name, doc in documents.iteritems():
        if not doc._meta['abstract'] and doc._is_document:
            doc.objects.delete()


def run(model='simple'):
    if model == 'clear_db':
        clear_db()

    init()
    init_items()
"""

    if os.path.isfile(path):
        with open(path) as fd:
            content = fd.read()

    items = "def init_items():\n    %s\n\n\n" % ('\n    '.join(items))
    content = re.sub(r"def init_items\(\):\n(.|\n)+?\n\n\n",
                     items, content)

    with open(path, 'w+') as fd:
        fd.write(content)


def get_project_name():
    if os.path.isfile('setup.py'):
        with open('setup.py') as fd:
            res = re.search('name=[\'"](.*)[\'"]', fd.read())
            if res:
                return res.group(1)


def create_command(info):
    def cmd(debug=False, reloader=False, host='0.0.0.0',
            port=info['config'].PORT):
        app = info['run']()
        app.run(debug=debug, use_reloader=reloader, host=host, port=port)
    return cmd


def main():
    global apps, commands

    project = None
    basename = os.path.basename(sys.argv[0])
    if basename != 'chiki':
        project = basename

    if not project:
        sys.path.append('.')
        project = get_project_name()

    if project:
        __import__(project)

    if 'manager' in apps:
        manager = Manager(apps['manager']['run'])

        for cmd, app in apps.iteritems():
            manager.add_command(cmd, Command(create_command(app)))

        for cmd, command in commands.iteritems():
            manager.add_command(cmd, Command(command))

        def make_shell_context():
            return dict(app=apps['manager']['run'](), db=db, um=um)

        manager.add_command("shell", Shell(make_context=make_shell_context))

        @manager.command
        @manager.option('name')
        def service(name, model='simple'):
            if not run_service(name, model):
                module = '%s.services.%s' % (project, name)
                action = __import__(module)
                for sub in module.split('.')[1:]:
                    action = getattr(action, sub)
                if inspect.getargspec(action.run)[0]:
                    action.run(model)
                else:
                    action.run()
    else:
        manager = Manager(Flask(__name__))

    @manager.command
    @manager.option('template')
    def create_project(template, checkout='', no_input=False,
                       api=False, web=False):
        context = dict(today=datetime.now().strftime('%Y-%m-%d'))
        if api:
            context['has_api'] = True
        if web:
            context['has_web'] = True
        cookiecutter(template, checkout, no_input, extra_context=context)

    manager.run()
