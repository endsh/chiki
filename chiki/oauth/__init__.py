# coding: utf-8
from .alipay import *
from .wxauth import *
from .wxpay import *
from .jssdk import *
from .robot import *
from .wxmsg import *
from .mini import *


def init_oauth(app):
    init_alipay(app)
    init_wxmsg(app)
    WXAuth.init(app)
    WXPay.init(app)
    Mini.init(app)
