# coding: utf-8
import os
import json
import time
import qrcode
import random
import traceback
from PIL import Image, ImageFont, ImageDraw
from StringIO import StringIO
from chiki.base import db, cache
from chiki.utils import today, retry
from datetime import datetime, timedelta
from flask import current_app
from flask.ext.login import current_user


class Enable(object):
    """ 状态选项 """

    DISABLED = 'disabled'
    DEBUG = 'debug'
    ENABLED = 'enabled'
    CHOICES = (
        (DISABLED, '停用'),
        (DEBUG, '调试'),
        (ENABLED, '发行'),
    )
    VALUES = [x for x, _ in CHOICES]
    DICT = dict(CHOICES)

    @staticmethod
    def get():
        if current_user.is_authenticated() and current_user.debug \
                or hasattr(current_app, 'enable_debug') and current_app.enable_debug():
            return [Enable.ENABLED, Enable.DEBUG]
        return [Enable.ENABLED]


class Item(db.Document):
    """ 选项 """

    MENU_ICON = 'gear'

    TYPE_INT = 'int'
    TYPE_STRING = 'string'
    TYPE_CHOICES = (
        (TYPE_INT, '整数'),
        (TYPE_STRING, '字符'),
    )

    name = db.StringField(max_length=40, verbose_name='名称')
    key = db.StringField(max_length=40, verbose_name='键名')
    type = db.StringField(default=TYPE_INT, choices=TYPE_CHOICES, verbose_name='类型')
    value = db.DynamicField(verbose_name='值')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            '-created',
        ]
    }

    @staticmethod
    @cache.memoize(timeout=5)
    def get(key, default=0, name=None):
        item = Item.objects(key=key).first()
        if item:
            return item.value

        Item(key=key, type=Item.TYPE_INT, value=default, name=name).save()
        return default

    @staticmethod
    def set(key, value, name=None):
        item = Item.objects(key=key).first()
        if not item:
            item = Item(key=key)

        if name:
            item.name = name
        item.type = Item.TYPE_INT
        item.value = value
        item.modified = datetime.now()
        item.save()

    @staticmethod
    def inc(key, default=0, num=1, name=None):
        query = dict(inc__value=num, set__modified=datetime.now())
        if name:
            query['set__name'] = name
        item = Item.objects(key=key).modify(**query)
        if not item:
            query = dict(key=key, type=Item.TYPE_INT, value=default + num)
            if name:
                query['name'] = name
            Item(**query).save()
            return default + num
        else:
            return item.value + num

    @staticmethod
    @cache.memoize(timeout=5)
    def data(key, default='', name=None):
        item = Item.objects(key=key).first()
        if item:
            return item.value

        Item(key=key, type=Item.TYPE_STRING, value=default, name=name).save()
        return default

    @staticmethod
    def set_data(key, value, name=None):
        item = Item.objects(key=key).first()
        if not item:
            item = Item(key=key)

        if name:
            item.name = name
        item.type = Item.TYPE_STRING
        item.value = value
        item.modified = datetime.now()
        item.save()

    @staticmethod
    def choice(key, value='', name=None, sep='|', coerce=str):
        return coerce(random.choice(Item.data(key, value, name).split(sep)))

    @staticmethod
    def list(key, value='', name=None, sep='|', coerce=int):
        return [coerce(x) for x in Item.data(key, value, name).split(sep)]

    @staticmethod
    def group(key, value='', name=None, sep='|', sub='-', coerce=int):
        texts = Item.data(key, value, name).split(sep)
        return [[coerce(y) for y in x.split(sub)] for x in texts]

    @staticmethod
    def hour(key, value='', name=None, sep='|', sub='-', default=None):
        h = datetime.now().hour
        for x in Item.group(key, value, name, sep, sub):
            if x[0] <= h <= x[1]:
                return x
        return default

    @staticmethod
    def bool(key, value=True, name=None):
        value = Item.data(key, 'true' if value else 'false', name)
        return True if value in ['true', 'True'] else False

    @staticmethod
    def time(key, value='', name=None):
        mat = "%Y-%m-%d %H:%M:%S"
        value = Item.data(key, datetime.now().strftime(mat), name)
        try:
            value = datetime.strptime(value, mat)
        except:
            pass
        return value


class Choice(db.EmbeddedDocument):
    """ 选项 """

    key = db.StringField(verbose_name='键名')
    name = db.StringField(verbose_name='名称')

    def __unicode__(self):
        return '%s - %s' % (self.key, self.name)


class Choices(db.Document):
    """ 选项模型 """

    MENU_ICON = 'plus-circle'

    fields = dict()
    key = db.StringField(verbose_name='键名')
    name = db.StringField(verbose_name='名称')
    default = db.StringField(verbose_name='默认值')
    choices = db.XListField(db.EmbeddedDocumentField(Choice), verbose_name='选项')
    enable = db.BooleanField(default=True, verbose_name='启用')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['key'])

    def __unicode__(self):
        return '%s - %s' % (self.key, self.name)

    @staticmethod
    def init():
        for key, field in Choices.fields.iteritems():
            Choices.init_field(key, field[1], field[0])

    @staticmethod
    def init_field(key, name, field, choices=None):
        choices = choices or Choices.objects(key=key).first()
        if choices:
            if choices.enable:
                if choices.default:
                    field.default = choices.default
                field.choices = [(x.key, x.name) for x in choices.choices]
            else:
                field.default = None
                field.choices = None
        else:
            Choices(key=key, name=name).save()
        Choices.refresh(field.owner_document)

    @staticmethod
    def refresh(model):
        if model:
            for admin in current_app.extensions.get('admin', []):
                for view in admin._views:
                    if model == getattr(view, 'model', None):
                        view._refresh_cache()

    def save(self):
        super(Choices, self).save()
        field = self.fields.get(self.key)
        if field:
            self.init_field(self.key, field[1], field[0], self)


def choice(field, key, name):
    Choices.fields[key] = (field, name)
    return field


db.dynamic = choice


class Share(db.EmbeddedDocument):
    """ 分享模型 """

    title = db.StringField(verbose_name='标题')
    content = db.StringField(verbose_name='描述')
    url = db.StringField(verbose_name='链接')
    image = db.XImageField(verbose_name='图片链接')

    def __unicode__(self):
        url = self.url
        if current_user.is_authenticated() and url.strip():
            if url and '?' in url:
                url = '%s&uid=%d' % (url, current_user.id)
            else:
                url = '%s?uid=%d' % (url, current_user.id)

        return json.dumps(dict(
            title=self.title,
            content=self.content,
            url=url,
            image=self.image.link,
        ))

    @staticmethod
    def get(share, title='', content='', url='', image=''):
        if share:
            title = share.title or title
            content = share.content or content
            url = share.url or url
            image = share.image.link or image

        if current_user.is_authenticated() and url.strip():
            if url and '?' in url:
                url = '%s&uid=%d' % (url, current_user.id)
            else:
                url = '%s?uid=%d' % (url, current_user.id)

        return json.dumps(dict(
            title=title,
            content=content,
            url=url,
            image=image,
        ))


class ShareLog(db.Document):
    """ 分享日志 """

    STATUS = db.choices(success='成功', cancel='取消', error='错误', fail='失败')
    MEDIA = db.choices(
        timeline='朋友圈', message='消息', qq='QQ', qzone='qzone', mini='小程序')

    user = db.ReferenceField('User', verbose_name='用户')
    media = db.StringField(verbose_name='平台', choices=MEDIA.CHOICES)
    title = db.StringField(verbose_name='标题')
    desc = db.StringField(verbose_name='描述')
    link = db.StringField(verbose_name='链接')
    image = db.StringField(verbose_name='图片')
    status = db.StringField(verbose_name='状态', choices=STATUS.CHOICES)
    # 小程序内容
    openGId = db.ListField(db.StringField(), verbose_name='GId')
    infos = db.StringField(verbose_name='infos')
    shareTickets = db.StringField(verbose_name='tickets')
    pos = db.StringField(verbose_name='分享位置')
    session_key = db.StringField(verbose_name='session_key')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'user',
            'link',
            '-created',
            ('status', 'created'),
            ('pos', 'created'),
            ('user', 'openGId', 'status', 'created'),
        ]
    }

    # 小程序解密专用
    def decrypt(self):
        # if not self.user or not self.user.wechat_user:
        #     return

        datas = json.loads(self.infos)
        for data in datas:
            if type(data) is dict and 'encryptedData' in data:
                encryptedData = data.get('encryptedData')
                iv = data.get('iv')
                if not encryptedData or not iv:
                    continue

                re = current_app.mini.decrypt(
                    self.session_key, encryptedData, iv)
                print 're: ', re
                if re['openGId']:
                    self.openGId.append(re['openGId'])
        self.save()


class StatLog(db.Document):
    """ 统计日志 """

    MENU_ICON = 'bar-chart'

    key = db.StringField(verbose_name='KEY')
    tid = db.StringField(verbose_name='TID')
    label = db.StringField(verbose_name='标签')
    day = db.StringField(verbose_name='日期')
    hour = db.IntField(default=0, verbose_name='小时')
    value = db.IntField(default=0, verbose_name='结果')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
            ('key', 'tid'),
            ('key', 'tid', 'day', 'hour'),
        ]
    }

    @staticmethod
    def inc(key, tid='', day=lambda: today(), hour=-1, value=1):
        if callable(day):
            day = day()
        day = str(day)[:10]
        item = StatLog.objects(key=key, tid=tid, day=day, hour=hour).modify(
            inc__value=value,
            set__modified=datetime.now(),
        )
        if not item:
            StatLog(key=key, tid=tid, day=day, hour=hour, value=value).save()
            return value
        else:
            return item.value + value

    @staticmethod
    def cinc(key, tid='', day=lambda: today(), hour=-1, value=1):
        if hasattr(current_app, 'redis'):
            if callable(day):
                day = day()
            day = str(day)[:10]
            cache_key = '|'.join(['StatLog', key, tid, day, str(hour)])
            cache_value = current_app.redis.get(cache_key)
            if cache_value:
                incr_value = current_app.redis.incr(cache_key, value)
                return int(incr_value + value)
            else:
                item = StatLog.objects(key=key, tid=tid, day=day, hour=hour).modify(
                    inc__value=value,
                    set__modified=datetime.now(),
                )
                if not item:
                    StatLog(key=key, tid=tid, day=day, hour=hour, value=value).save()
                    current_app.redis.set(cache_key, value)
                    return value
                else:
                    current_app.redis.set(cache_key, item.value)
                    return item.value + value
        return StatLog.inc(key, tid, day, hour, value)

    @staticmethod
    def get(key, tid='', day=lambda: today(), hour=-1, default=0, save=True):
        if callable(day):
            day = day()
        day = str(day)[:10]
        item = StatLog.objects(key=key, tid=tid, day=day, hour=hour).first()
        if item:
            return item.value

        if save:
            StatLog(key=key, tid=tid, day=day, hour=hour, value=default).save()
        return default

    @staticmethod
    def cget(key, tid='', day=lambda: today(), hour=-1, default=0, save=True):
        if hasattr(current_app, 'redis'):
            if callable(day):
                day = day()
            day = str(day)[:10]
            cache_key = '|'.join(['StatLog', key, tid, day, str(hour)])
            cache_value = current_app.redis.get(cache_key)
            if cache_value:
                return int(cache_value)
            else:
                item = StatLog.objects(key=key, tid=tid, day=day, hour=hour).first()
                if item:
                    current_app.redis.set(cache_key, item.value)
                    return item.value
                if save:
                    StatLog(key=key, tid=tid, day=day, hour=hour, value=default).save()
                    current_app.redis.set(cache_key, default)
                return default
        return StatLog.get(key, tid, day, hour, default, save)

    @staticmethod
    def date_inc(key, tid='', label='', value=1, day=None):
        day = time.strftime('%Y-%m-%d') if not day else day
        item = StatLog.objects(key=str(key), tid=tid, label=label, day=day, hour=-1).modify(
            inc__value=value,
            set__modified=datetime.now(),
        )
        if not item:
            StatLog(key=str(key), tid=tid, label=label, day=day, hour=-1, value=value).save()
            return value
        else:
            return item.value + value

    @staticmethod
    def date_set(key, tid='', label='', value=1, day=None):
        day = time.strftime('%Y-%m-%d') if not day else day
        item = StatLog.objects(key=str(key), tid=tid, label=label, day=day, hour=-1).modify(
            value=value,
            set__modified=datetime.now(),
        )
        if not item:
            StatLog(key=str(key), tid=tid, label=label, day=day, hour=-1, value=value).save()
        return value

    @staticmethod
    def date_get(key, tid='', label='', day=None):
        day = time.strftime('%Y-%m-%d') if not day else day
        log = StatLog.objects(key=str(key), tid=tid, label=label, day=day, hour=-1).first()
        return log.value if log else 0

    @staticmethod
    def xinc(key, tid='', day='', hour=-1, value=1):
        return StatLog.inc(key, tid, day, hour, value)

    @staticmethod
    def xget(key, tid='', day='', hour=-1, default=0, save=True):
        return StatLog.get(key, tid, day, hour, default, save)

    @staticmethod
    def date_limit(key, tid='', label='',
                   limit=timedelta(days=1), default=0, save=True):
        if type(limit) == int:
            limit = timedelta(days=limit)
        log = StatLog.objects(key=str(key), tid=tid, label=label,
                              day='', hour=-1).first()
        if not log:
            if save:
                StatLog(key=str(key), tid=tid, label=label,
                        day='', hour=-1).save()
            return True
        if log.modified + limit < datetime.now():
            log.modified = datetime.now()
            log.save()
            return True
        return False


class TraceLog(db.Document):
    """ 监控统计 """

    MENU_ICON = 'bug'

    user = db.ReferenceField('User', verbose_name='用户')
    key = db.StringField(verbose_name='KEY')
    tid = db.StringField(verbose_name='TID')
    label = db.StringField(verbose_name='标识')
    value = db.StringField(verbose_name='结果')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            'tid',
            'user',
            'label',
            '-created',
            ('key', '-created'),
        ]
    }


def create_mini_code(model, content):
    try:
        conf = current_app.config.get("MINI_CODE_BG", {})
        path = current_app.get_data_path(conf.get('path'))
        with open(path) as fd:
            bg = Image.open(StringIO(fd.read()))
        im = Image.open(StringIO(content))
        im = im.resize((conf.get('width'), conf.get('width')), Image.ANTIALIAS)
        bg.paste(im, (conf.get('x'), conf.get('y')))

        draw = ImageDraw.Draw(bg)
        default = current_app.get_data_path('fonts/yh.ttf')
        if os.path.isfile(default):
            size = 18
            font = ImageFont.truetype(default, size)
            x = 10
            y = 10
            draw.text((x, y), 'ID: ' + str(model.id), font=font, fill='#ffffff')
            del draw

        stream = StringIO()
        bg.save(stream, format='png')
        return dict(stream=stream, format='png')
    except:
        current_app.logger.error(traceback.format_exc())


class Channel(db.Document):
    """ 渠道模型 """

    MENU_ICON = 'road'

    id = db.IntField(primary_key=True, verbose_name='ID')
    name = db.StringField(max_length=40, verbose_name='名称')
    password = db.StringField(max_length=40, verbose_name='密码')
    desc = db.StringField(verbose_name='描述')
    url = db.StringField(verbose_name='链接')
    image = db.XImageField(verbose_name='二维码')
    active = db.BooleanField(default=True, verbose_name='激活')
    sid = db.IntField(verbose_name='源渠道号')
    appid = db.StringField(verbose_name='AppId')
    label = db.StringField(verbose_name='标签')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'sid',
            'appid',
            'label',
            '-created',
        ]
    }

    def is_user(self):
        return True

    def is_authenticated(self):
        """ 是否登录 """
        return True

    def is_active(self):
        """ 是否激活 """
        return True

    def is_anonymous(self):
        """ 是否游客 """
        return False

    def get_id(self):
        """ 获取用户ID """
        return '%s:%s' % ('channel', str(self.id))

    def create(self):
        """ 创建渠道 """
        if not self.id:
            self.id = Item.inc('channel_index', 1000)
            self.save()
        return self.id

    def create_image(self, force=False):
        if hasattr(current_app, 'mini'):
            if not self.image or force:
                content = current_app.mini.create_code(
                    '?type=ad&pos=code&uid=%d&channel=%d' % (self.id, self.id))
                self.image = create_mini_code(self, content)
                self.save()


class QRCode(db.Document):
    """ 二维码 """

    MENU_ICON = 'qrcode'

    user = db.ReferenceField('User', verbose_name='用户')
    url = db.StringField(verbose_name='链接')
    image = db.XImageField(verbose_name='二维码')
    scene = db.StringField(verbose_name='场景')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['user', '-created'])

    @staticmethod
    def get(user, url=None, config=None, scene=None):
        qr = QRCode.objects(user=user.id, scene=scene).first()
        if not qr:
            qr = QRCode(user=user.id, url=url, scene=scene)
            qr.save()

        if url and qr.url != url:
            qr.url = url
            qr.image = None

        if not config:
            config = current_app.config.get('QRCODE', {})
        if type(config) is list:
            config = random.choice(config)
        if config.get('wxclient', True) and (
                not qr.url or datetime.now() > qr.modified + timedelta(days=25)):
            data = dict(
                expire_seconds=2592000,
                action_name='QR_SCENE',
                action_info=dict(scene=dict(scene_id=user.id)),
            )
            qr.url = current_app.wxclient.create_qrcode(**data).get('url')
            qr.modified = datetime.now()

        if qr.url and not qr.image:
            @retry(3)
            def simple():
                qr.create_image(user, config)

        qr.save()
        return qr

    def create_qrcode(self, config):
        logo = config.get('logo', current_app.get_data_path('imgs/logo.jpg'))
        A, B, C = 250, 66, 58
        qr = qrcode.QRCode(version=2, box_size=10, border=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(self.url)
        qr.make(fit=True)
        im = qr.make_image()
        im = im.convert("RGBA")
        im = im.resize((A, A), Image.BILINEAR)

        if config.get('qr_logo', True):
            em = Image.new("RGBA", (B, B), "white")
            im.paste(em, ((A - B) / 2, (A - B) / 2), em)

            with open(logo) as fd:
                icon = Image.open(StringIO(fd.read()))
            icon = icon.resize((C, C), Image.ANTIALIAS)
            icon = icon.convert("RGBA")
            im.paste(icon, ((A - C) / 2, (A - C) / 2), icon)

        qr_width = config.get('qr_width', im.size[0])
        im = im.resize((qr_width, qr_width), Image.BILINEAR)
        return im

    def create_bg(self, config, user, qr):
        logo = config.get('logo', current_app.get_data_path('imgs/logo.jpg'))
        bgpath = config.get('bg')
        if bgpath:
            with open(bgpath) as fd:
                bg = Image.open(StringIO(fd.read()))
            qr_x = config.get('qr_x', (bg.size[0] - qr.size[0]) / 2)
            qr_y = config.get('qr_y', bg.size[1] / 2)

            bg.convert("RGBA")
            bg.paste(qr, (qr_x, qr_y), qr)

            avatar_show = config.get('avatar_show', True)
            if not avatar_show:
                return bg

            if user.avatar:
                ic = Image.open(StringIO(user.avatar.content))
            else:
                with open(logo) as fd:
                    ic = Image.open(StringIO(fd.read()))

            avatar_width = config.get('avatar_width', ic.size[0])
            avatar_x = config.get('avatar_x', (bg.size[0] - avatar_width) / 2)
            avatar_y = config.get('avatar_y', bg.size[1] / 2)
            ic = ic.resize((avatar_width, avatar_width), Image.ANTIALIAS)
            ic = ic.convert("RGBA")

            if config.get('avatar_circle', False):
                bigsize = (ic.size[0] * 3, ic.size[1] * 3)
                mask = Image.new('L', bigsize, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0) + bigsize, fill=255)
                del draw
                mask = mask.resize(ic.size, Image.ANTIALIAS)
                ic.putalpha(mask)
            bg.paste(ic, (avatar_x, avatar_y), ic)
            return bg
        return qr

    def replace(self, text, user):
        return text

    def textsize(self, user, draw, font, width, texts):
        w, has_nick = 0, False
        for text in texts:
            if type(text) in [list, tuple]:
                text = text[0]

            if '<nickname>' in text:
                has_nick = True

            text = text.replace('<id>', str(user.id))
            text = text.replace('<tid>', user.tid)
            text = text.replace('<nickname>', user.nickname or '佚名')
            text = text.replace('<expire>', (
                self.modified + timedelta(days=30)).strftime('%Y-%m-%d'))
            text = self.replace(text, user)
            w += draw.textsize(text, font=font)[0]

        nickname = user.nickname or '佚名'
        limit = len(nickname)
        if has_nick:
            nick_width = draw.textsize(nickname, font=font)[0]
            while limit > 4 and width - w + draw.textsize(
                    nickname[:limit], font=font)[0] < nick_width:
                limit -= 1
            w += draw.textsize(nickname[:limit], font=font)[0] - nick_width
        return (width - w) / 2, limit

    def draw_texts(self, config, user, bg):
        draw = ImageDraw.Draw(bg)
        default = config.get('font', current_app.get_data_path('fonts/yh.ttf'))
        for line in config.get('lines', []):
            size = line.get('size', 18)
            font = ImageFont.truetype(line.get('font', default), size)
            x = line.get('x', 0)
            y = line.get('y', 0)

            texts = line.get('texts', [])
            nickname = user.nickname or '佚名'
            limit = len(nickname)
            if x == 'center':
                x, limit = self.textsize(user, draw, font, bg.size[0], texts)

            for text in texts:
                color = line.get('color', '#333333')
                if type(text) in [list, tuple]:
                    text, color = text[0], text[1]
                text = text.replace('<id>', str(user.id))
                text = text.replace('<tid>', user.tid)
                text = text.replace('<nickname>', nickname[:limit])
                text = text.replace('<expire>', (
                    self.modified + timedelta(days=30)).strftime('%Y-%m-%d'))
                text = self.replace(text, user)
                width, _ = draw.textsize(text, font=font)
                draw.text((x, y), text, font=font, fill=color)
                x += width
        del draw
        return bg

    def create_image(self, user, config=None):
        if not config:
            config = current_app.config.get('QRCODE', {})

        if type(config) is list:
            config = random.choice(config)
        qr = self.create_qrcode(config)
        bg = self.create_bg(config, user, qr)
        bg = self.draw_texts(config, user, bg)
        stream = StringIO()
        bg.save(stream, format='png')
        self.image = dict(stream=stream, format='png')
        self.save()


class AndroidVersion(db.Document):
    """ 安卓版本 """

    MENU_ICON = 'android'

    id = db.IntField(primary_key=True, verbose_name='ID')
    version = db.StringField(max_length=200, verbose_name='版本')
    log = db.StringField(verbose_name='更新日志')
    url = db.StringField(verbose_name='应用地址')
    force = db.StringField(verbose_name='强制更新')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    def __unicode__(self):
        return '%d - %s' % (self.id, self.version)

    def create(self):
        """ 创建版本 """
        if not self.id:
            self.id = Item.inc('android_version_index', 100)
            self.save()
        return self.id


class IOSVersion(db.Document):
    """ IOS版本 """

    MENU_ICON = 'mobile'

    id = db.IntField(primary_key=True, verbose_name='ID')
    version = db.StringField(max_length=200, verbose_name='版本')
    log = db.StringField(verbose_name='更新日志')
    url = db.StringField(verbose_name='应用地址')
    force = db.StringField(verbose_name='强制更新')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    def __unicode__(self):
        return '%d - %s' % (self.id, self.version)

    def create(self):
        """ 创建版本 """
        if not self.id:
            self.id = Item.inc('ios_version_index', 100)
            self.save()
        return self.id


class API(db.Document):
    """ 接口模型 """

    MENU_ICON = 'server'

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    url = db.StringField(verbose_name='链接')
    expire = db.IntField(default=0, verbose_name='缓存')
    cache = db.BooleanField(verbose_name='已缓存')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }

    @property
    def detail(self):
        return dict(
            name=self.name,
            key=self.key,
            url=self.url,
            expire=self.expire,
            cache=self.cache,
        )


class Icon(db.Document):
    """ 图标模型 """

    MENU_ICON = 'picture-o'

    icon = db.Base64ImageField(verbose_name='图标')
    key = db.StringField(verbose_name='ID')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            '-created',
        ]
    }


class Action(db.Document):
    """ 功能模型 """

    MENU_ICON = 'bars'

    key = db.StringField(verbose_name='ID')
    name = db.StringField(verbose_name='名称')
    desc = db.StringField(verbose_name='描述')
    icon = db.Base64ImageField(verbose_name='图标')
    active_icon = db.Base64ImageField(verbose_name='激活图标')
    module = choice(db.StringField(verbose_name='模块'), 'action_module', '功能模块')
    data = db.StringField(verbose_name='数据')
    target = db.StringField(verbose_name='目标')
    share = db.EmbeddedDocumentField(Share, verbose_name='分享')
    sort = db.IntField(verbose_name='排序')
    android_start = db.ReferenceField(AndroidVersion, verbose_name='安卓版本')
    android_end = db.ReferenceField(AndroidVersion, verbose_name='安卓最大版本')
    ios_start = db.ReferenceField(IOSVersion, verbose_name='IOS版本')
    ios_end = db.ReferenceField(IOSVersion, verbose_name='IOS最大版本')
    login = db.BooleanField(default=False, verbose_name='登陆')
    login_show = db.BooleanField(default=False, verbose_name='显示')
    debug = db.BooleanField(default=False, verbose_name='调试')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            'sort',
            '-created',
        ]
    }

    @property
    def detail(self):
        return dict(
            id=self.key,
            name=self.name,
            desc=self.desc,
            icon=self.icon.base64,
            active_icon=self.active_icon.base64,
            data=self.data,
            target=self.target,
            share=unicode(self.share),
            login=self.login,
            login_show=self.login_show,
            debug=self.debug,
        )


class TPL(db.Document):
    """ 模板模型 """

    MENU_ICON = 'globe'

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    tpl = db.XFileField(verbose_name='文件', allows=['html', 'htm'])
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')


class Slide(db.Document):
    """ 广告模型 """

    MENU_ICON = 'paw'

    key = db.StringField(verbose_name='ID')
    name = db.StringField(verbose_name='名称')
    icon = db.XImageField(verbose_name='图标')
    module = choice(db.StringField(verbose_name='模块'), 'slide_module', '广告模块')
    target = db.StringField(verbose_name='目标')
    share = db.EmbeddedDocumentField(Share, verbose_name='分享')
    sort = db.IntField(verbose_name='排序')
    android_start = db.ReferenceField(AndroidVersion, verbose_name='安卓版本')
    android_end = db.ReferenceField(AndroidVersion, verbose_name='安卓最大版本')
    ios_start = db.ReferenceField(IOSVersion, verbose_name='IOS版本')
    ios_end = db.ReferenceField(IOSVersion, verbose_name='IOS最大版本')
    login = db.BooleanField(default=False, verbose_name='登陆')
    login_show = db.BooleanField(default=False, verbose_name='显示')
    debug = db.BooleanField(default=False, verbose_name='调试')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'key',
            'sort',
            '-created',
        ]
    }

    @property
    def detail(self):
        return dict(
            id=self.key,
            name=self.name,
            icon=self.icon.link,
            target=self.target,
            share=unicode(self.share),
            login=self.login,
            login_show=self.login_show,
            debug=self.debug,
        )


class AD(db.Document):
    """ 广告 """

    MENU_ICON = 'paw'

    name = db.StringField(verbose_name='名称')
    image = db.XImageField(verbose_name='图片')
    link = db.StringField(verbose_name='链接')
    sort = db.IntField(verbose_name='排序')
    module = choice(db.StringField(verbose_name='模块'), 'ad_module', '广告模块')
    enable = db.StringField(default=Enable.ENABLED,
                            choices=Enable.CHOICES, verbose_name='状态')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    TPL = '<a class="ad-image" href="%s" target="_blank"><img src="%s"></a>'

    meta = dict(indexes=[('module', 'enable', '-created')])

    def __nonzero__(self):
        return bool(self.link.strip())

    @property
    def html(self):
        if self.image.link:
            return self.TPL % (self.link.strip(), self.image.link)
        return self.link.strip()

    @property
    def json(self):
        return dict(
            name=self.name,
            image=self.image.link,
            link=self.link,
        )


class UserImage(db.Document):
    """ 用户图片 """

    MENU_ICON = 'picture-o'

    user = db.ReferenceField('User', verbose_name='用户')
    source = db.StringField(verbose_name='来源')
    image = db.XImageField(verbose_name='图片')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = {
        'indexes': [
            'source',
            '-created',
        ]
    }


class ImageItem(db.Document):
    """ 图片模型 """

    MENU_ICON = 'picture-o'

    key = db.StringField(verbose_name='key')
    name = db.StringField(verbose_name='名称')
    image = db.XImageField(verbose_name='图片')
    type = choice(db.StringField(verbose_name='模块'), 'image_module', '图片模块')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return '%s-%s' % (self.key, self.name)

    @staticmethod
    def get(key, name='默认', size=tuple()):
        image = ImageItem.objects(key=key).order_by('-create').first()
        if not image:
            image = ImageItem(
                key=key, name=name
            ).save()
        return image.image.get_link(*size) if image.image else ''

    @staticmethod
    def get_type_qrcodes(_type='other'):
        return list(ImageItem.objects(type=_type).all())

    @staticmethod
    def get_type_qrcode(_type='other'):
        images = ImageItem.get_type_qrcodes(_type)
        if not images:
            return None
        return random.choice(images)

    def create(self):
        """ 创建用户 """
        if not self.key:
            self.key = '%s' % Item.inc('image_index', 1000)
            self.save()
        return self.key


class Option(db.Document):
    """ 配置模型 """

    MENU_ICON = 'gear'

    name = db.StringField(verbose_name='名称')
    key = db.StringField(verbose_name='键名')
    value = db.StringField(verbose_name='值')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['-created'])


class Menu(db.Document):
    """ 菜单模型 """

    MENU_ICON = 'sitemap'

    key = db.StringField(verbose_name='键名')
    name = db.StringField(verbose_name='名称')
    link = db.StringField(verbose_name='链接')
    icon = db.XImageField(verbose_name='图标')
    module = choice(db.StringField(verbose_name='模块'), 'menu_module', '菜单模块')
    sort = db.IntField(verbose_name='排序')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=[('enable', 'module', 'sort')])

    @staticmethod
    def get(module):
        return Menu.objects(module=module, enable=Enable.get()).order_by('sort')


class Page(db.Document):
    """ 网页模型 """

    MENU_ICON = 'globe'

    id = db.IntField(primary_key=True, verbose_name='ID')
    key = db.StringField(verbose_name='键名')
    bg = db.StringField(verbose_name='背景颜色(#FFF)')
    padding = db.BooleanField(default=False, verbose_name="内边距")
    style = db.StringField(verbose_name="样式")
    name = db.StringField(verbose_name='名称')
    content = db.StringField(verbose_name='正文')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['-created'])

    def create(self):
        """ 创建用户 """
        if not self.id:
            self.id = Item.inc('page_index', 1000)
            self.save()
        return self.id


class Field(db.EmbeddedDocument):
    """ 选项 """

    TYPE_INT = 'IntField'
    TYPE_STRING = 'StringField'
    TYPE_REF = 'ReferenceField'
    TYPE_IMAGE = 'XImageField'
    TYPE_FILE = 'XFileField'
    TYPE_DATETIME = 'DateTimeField'
    TYPE_BOOL = 'BooleanField'
    TYPE_CHOICES = [
        (TYPE_INT, TYPE_INT),
        (TYPE_STRING, TYPE_STRING),
        (TYPE_REF, TYPE_REF),
        (TYPE_IMAGE, TYPE_IMAGE),
        (TYPE_FILE, TYPE_FILE),
        (TYPE_DATETIME, TYPE_DATETIME),
        (TYPE_BOOL, TYPE_BOOL),
    ]

    key = db.StringField(max_length=100, verbose_name='键名')
    type = db.StringField(default=TYPE_INT, choices=TYPE_CHOICES, verbose_name='类型')
    name = db.StringField(max_length=100, verbose_name='名称')
    default = db.StringField(max_length=100, verbose_name='默认值')
    model = db.ReferenceField('Model', verbose_name='引用')
    choices = db.ReferenceField('Choices', verbose_name='选项')

    def __unicode__(self):
        return '%s - %s' % (self.key, self.name)


class Model(db.Document):
    """ 建模 """

    MENU_ICON = 'database'

    name = db.StringField(max_length=100, verbose_name='名称')
    desc = db.StringField(max_length=100, verbose_name='描述')
    fields = db.XListField(db.EmbeddedDocumentField(Field), verbose_name='字段')
    modified_field = db.BooleanField(default=True, verbose_name='修改')
    created_field = db.BooleanField(default=True, verbose_name='创建')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return self.name

    @property
    def can_create(self):
        if current_user.is_authenticated():
            group = current_user.group
            name = self.__class__.__name__
            if current_user.root is True \
                    or getattr(self, 'can_use', False) is True \
                    or group and name in group.power_list \
                    and name in group.can_create_list:
                return self._can_create
        return False

    @property
    def can_edit(self):
        if current_user.is_authenticated():
            group = current_user.group
            name = self.__class__.__name__
            if current_user.root is True \
                    or getattr(self, 'can_use', False) is True \
                    or group and name in group.power_list \
                    and name in group.can_edit_list:
                return self._can_edit
        return False

    @property
    def can_delete(self):
        if current_user.is_authenticated():
            group = current_user.group
            name = self.__class__.__name__
            if current_user.root is True \
                    or getattr(self, 'can_use', False) is True \
                    or group and name in group.power_list \
                    and name in group.can_delete_list:
                return self._can_delete
        return False


class View(db.Document):
    """ 管理 """

    MENU_ICON = 'futbol-o'

    TYPE_VIEW = 'view'
    TYPE_MODEL = 'model'
    TYPE_CATE = 'cate'
    TYPE_CHOICES = [
        (TYPE_VIEW, '默认'),
        (TYPE_MODEL, '模型'),
        (TYPE_CATE, '分类'),
    ]

    name = db.StringField(max_length=100, verbose_name='名称')
    label = db.StringField(max_length=100, verbose_name='标识')
    type = db.StringField(default=TYPE_VIEW, choices=TYPE_CHOICES, verbose_name='类型')
    model = db.ReferenceField('Model', verbose_name='模型')
    icon = db.StringField(max_length=100, verbose_name='图标')
    page_size = db.IntField(default=50, verbose_name='分页数')
    can_create = db.BooleanField(default=True, verbose_name='能创建')
    can_edit = db.BooleanField(default=True, verbose_name='能修改')
    can_delete = db.BooleanField(default=True, verbose_name='能删除')
    column_default_sort = db.StringField(max_length=100, verbose_name='默认排序')
    column_list = db.ListField(db.StringField(), verbose_name='显示列表')
    column_center_list = db.ListField(db.StringField(), verbose_name='居中列表')
    column_hidden_list = db.ListField(db.StringField(), verbose_name='隐藏列表')
    column_filters = db.ListField(db.StringField(), verbose_name='过滤器列表')
    column_sortable_list = db.ListField(db.StringField(), verbose_name='排序列表')
    column_searchable_list = db.ListField(db.StringField(), verbose_name='查找列表')
    form_excluded_columns = db.ListField(db.StringField(), verbose_name='表单隐藏列表')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    def __unicode__(self):
        return self.name

    def setup(self, admin, view):
        view.name = self.label or view.name
        view.menu_icon_value = self.icon or view.menu_icon_value
        if hasattr(view, 'model'):
            if not view.menu_icon_value:
                if view.model and hasattr(view.model, 'MENU_ICON'):
                    view.menu_icon_value = view.model.MENU_ICON
                else:
                    view.menu_icon_value = 'file-o'

            view._can_create = view.can_create
            view._can_edit = view.can_edit
            view._can_delete = view.can_delete

            setattr(view.__class__, 'can_create', can_create)
            setattr(view.__class__, 'can_edit', can_edit)
            setattr(view.__class__, 'can_delete', can_delete)

            # view.page_size = self.page_size or view.page_size
            # view.can_create = self.can_create
            # view.can_edit = self.can_edit
            # view.can_delete = self.can_delete
            # if self.column_default_sort:
            #     try:
            #         view.column_default_sort = json.loads(self.column_default_sort)
            #     except:
            #         pass
            # view.column_list = self.column_list or view.column_list
            # view.column_center_list = self.column_center_list or getattr(view, 'column_center_list', None)
            # view.column_hidden_list = self.column_hidden_list or getattr(view, 'column_hidden_list', None)
            # view.column_filters = self.column_filters or view.column_filters
            # view.column_sortable_list = self.column_sortable_list or view.column_sortable_list
            # view.column_searchable_list = self.column_searchable_list or view.column_searchable_list
            # view.form_excluded_columns = self.form_excluded_columns or view.form_excluded_columns
            # view._refresh_cache()
        elif not view.menu_icon_value:
            if hasattr(view, 'MENU_ICON'):
                view.menu_icon_value = view.MENU_ICON
        admin._refresh()

    def save(self):
        super(View, self).save()

        if current_app.cool_manager and not current_app.cool_manager.loading:
            for admin in current_app.extensions.get('admin', []):
                for view in admin._views:
                    if view.__class__.__name__ == self.name:
                        self.setup(admin, view)
                        break

    def add_text(self, key):
        attr = getattr(self, key)
        if attr:
            return '    %s = %s' % (key, json.dumps(attr))

    @property
    def code_text(self):
        texts = []
        keys = ['column_list', 'column_center_list', 'column_hidden_list',
                'column_filters', 'column_sortable_list', 'column_searchable_list',
                'form_excluded_columns']
        for key in keys:
            text = self.add_text(key)
            if text:
                texts.append(text)
        return '\n'.join(texts)


class IP(db.Document):
    """ IP名单 """

    MENU_ICON = 'wifi'
    TYPE = db.choices(register='注册', sms='短信')

    ip = db.StringField(verbose_name='IP')
    type = db.StringField(default=TYPE.REGISTER, choices=TYPE.CHOICES, verbose_name='类型')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['-created', ('type', 'ip')])


class Log(db.Document):
    """ 运行日志 """

    name = db.StringField(verbose_name='名称')
    levelname = db.StringField(verbose_name='等级')
    thread = db.IntField(verbose_name='进程')
    threadName = db.StringField(verbose_name='进程名称')
    module = db.StringField(verbose_name='模块')
    funcName = db.StringField(verbose_name='方法')
    lineno = db.IntField(verbose_name='行号')
    message = db.StringField(verbose_name='信息')
    exc = db.StringField(verbose_name='异常')
    url = db.StringField(verbose_name='链接')
    user_agent = db.StringField(verbose_name='UA')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=['-created', 'levelname', 'url', 'message', 'user_agent'])


class Complaint(db.Document):
    """ 投诉记录 """

    TYPE = db.choices(
        dec='欺骗', por='色情', pol='政治谣言', common='常识性谣言', share='分享诱导',
        mal='恶意营销', other='其他侵权类（冒名，诽谤，抄袭')

    user = db.ReferenceField('User', verbose_name='用户')
    id = db.StringField(primary_key=True, verbose_name='ID')
    type = db.StringField(
        default=TYPE.OTHER, choices=TYPE.CHOICES, verbose_name='类型')
    content = db.StringField(verbose_name='内容')
    active = db.BooleanField(default=False, verbose_name='封号')
    result = db.StringField(verbose_name='处理结果')
    remark = db.StringField(verbose_name='备注')
    handle = db.DateTimeField(default=datetime.now, verbose_name='处理时间')
    modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=[
        ('user', '-created'),
        '-created'
    ])

    def create(self):
        """ 创建 """
        if not self.id:
            self.id = '{:%Y%m%d}{:0>8}'.format(
                datetime.now(), StatLog.date_inc('complaint_id'))
            self.save()
        return self.id


class MiniTPLLog(db.Document):
    """ 小程序模板消息日志 """
    STATUS = db.choices(success='成功', error='错误')

    user = db.ReferenceField('User', verbose_name='接收者')
    template_id = db.StringField(verbose_name='模板id')
    page = db.StringField(verbose_name='跳转url')
    form_id = db.StringField(verbose_name='订单')
    data = db.StringField(verbose_name='内容')
    color = db.StringField(verbose_name='字体颜色')
    emphasis_keyword = db.StringField(verbose_name='关键词')
    status = db.StringField(default=STATUS.ERROR, verbose_name='状态',
                            choices=STATUS.CHOICES)
    msg = db.StringField(verbose_name='错误信息')
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(indexes=[
        ('user', '-created'),
        '-created'
    ])

    @staticmethod
    def send_tpl(user, tpl, form_id, url, data):
        openid = ''
        if user.wechat_user:
            openid = user.wechat_user.mini_openid
        mini = MiniTPLLog(
            user=user,
            template_id=tpl,
            page=url,
            form_id=form_id,
            data=json.dumps(data),
        )
        res = current_app.mini.client.send_mini_tpl(openid, tpl, form_id, url, data)
        mini.msg = json.dumps(res)
        if res['errcode'] == 0:
            mini.status = MiniTPLLog.STATUS.SUCCESS
        mini.save()
        return mini.id
