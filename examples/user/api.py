# coding: utf-8
import sys
sys.path.append('../..')

from chiki import init_api
from chiki.api import api
from chiki.contrib.users import UserManager


class Config(object):
    pass


def init(app):
    user = UserManager(app)
    user.init_apis(api)
    api.init_app(app)


app = init_api(init, Config)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
