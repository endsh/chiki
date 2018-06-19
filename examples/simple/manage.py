# coding: utf-8
import inspect
from flask.ext.script import Manager, Server
from simple import create_admin, create_api, create_web
from simple.config import BaseConfig, AdminConfig, APIConfig, WebConfig

manager = Manager(create_admin)
manager.add_command('admin', Server(port=AdminConfig.PORT))


@manager.command
def api(debug=False, reloader=False, host='0.0.0.0', port=APIConfig.PORT):
    """ Run the api server. """
    app = create_api()
    app.run(debug=debug, use_reloader=reloader, host=host, port=port)


@manager.command
def web(debug=False, reloader=False, host='0.0.0.0', port=WebConfig.PORT):
    """ Run the web server. """
    app = create_web()
    app.run(debug=debug, use_reloader=reloader, host=host, port=port)


@manager.command
def test():
    """ Run the tests. """
    import pytest
    exit_code = pytest.main([BaseConfig.TEST_FOLDER])
    return exit_code


@manager.command
@manager.option('name')
def service(name, model='simple'):
    module = 'simple.services.%s' % name
    action = __import__(module)
    for sub in module.split('.')[1:]:
        action = getattr(action, sub)
    if inspect.getargspec(action.run)[0]:
        action.run(model)
    else:
        action.run()


if __name__ == '__main__':
    manager.run()
