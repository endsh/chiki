# coding: utf-8
from requests.packages import urllib3
urllib3.disable_warnings()

from datetime import datetime
from ..base import db
from chiki.contrib.common.models import Action, Share


class PushLog(db.Document):
    """ 推送日志 """

    TYPE = db.choices(
        sync='刷新缓存', sync_userinfo='同步用户数据', sync_update='软件更新',
        sync_money='同步收益', action='点击事件', other='其他',
    )

    user = db.IntField(verbose_name='用户')
    type = db.StringField(default=TYPE.SYNC, choices=TYPE.CHOICES, verbose_name='类型')
    data = db.StringField(verbose_name='数据')
    title = db.StringField(verbose_name='标题')
    alert = db.StringField(verbose_name='内容')
    code = db.IntField(verbose_name='状态码')
    created = db.DateTimeField(default=lambda: datetime.now(), verbose_name='创建时间')

    meta = {
        'indexes': [
            'user',
            'created',
        ],
    }


class PushAction(db.Document):
    """ 推送功能 """

    TYPE = db.choices(
        default='原生', empty='无动作', tablist='Tab', webstatic='静态网页',
        webview='网页', listview='列表', gridview='表格', article_listview='文章列表',
        browser='浏览器', redirect='内部跳转', divider='分割线',
    )

    key = db.StringField(verbose_name='键名')
    name = db.StringField(verbose_name='名称')
    action = db.StringField(default=TYPE.DEFAULT, verbose_name='动作', choices=TYPE.CHOICES)
    url = db.StringField(verbose_name='链接')
    share = db.EmbeddedDocumentField(Share, verbose_name='分享')
    created = db.DateTimeField(default=lambda: datetime.now(), verbose_name='创建时间')


class PushAllLog(db.Document):
    """全员推送日志"""

    TYPE = db.choices(
        sync='刷新缓存', sync_userinfo='同步用户数据', sync_update='软件更新',
        sync_money='同步收益', action='点击事件', other='其他',
    )

    type = db.StringField(default=TYPE.SYNC, choices=TYPE.CHOICES, verbose_name='类型')
    data = db.StringField(verbose_name='数据')
    title = db.StringField(verbose_name='标题')
    alert = db.StringField(verbose_name='内容')
    code = db.IntField(verbose_name='状态码')
    created = db.DateTimeField(default=lambda: datetime.now(), verbose_name='创建时间')
