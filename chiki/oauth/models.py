#coding: utf-8
from chiki.base import db
from datetime import datetime
from werobot.reply import Article, ArticlesReply, TextReply, MusicReply
from chiki.contrib.common import Enable


class Second(db.EmbeddedDocument):
    """ 二级菜单 """

    name = db.StringField(verbose_name='标题')
    url = db.StringField(verbose_name='链接')

    def __unicode__(self):
        return '%s-%s' % (self.name, self.url)


class WXMenu(db.Document):
    """ 微信菜单 """

    name = db.StringField(verbose_name='主菜单')
    second = db.ListField(db.EmbeddedDocumentField(Second), verbose_name='二级菜单')
    url = db.StringField(verbose_name='链接')
    sort = db.IntField(verbose_name='排序')
    make = db.BooleanField(verbose_name='使用', default=False)
    created = db.DateTimeField(verbose_name='创建时间', default=datetime.now)


class ArticleItem(db.EmbeddedDocument):

    title = db.StringField(verbose_name='标题')
    description = db.StringField(verbose_name='描述')
    img = db.XImageField(verbose_name='图片链接')
    url = db.StringField(verbose_name='跳转链接')


class MusicItem(db.EmbeddedDocument):

    title = db.StringField(verbose_name='标题')
    desc = db.StringField(verbose_name='描述')
    url = db.XFileField(allows=['mp3', 'wma', 'rm', 'mid'], verbose_name='链接')
    hq_url = db.XFileField(allows=['mp3', 'wma', 'rm', 'mid'], verbose_name='高质量链接')


class Message(db.Document):
    """ 消息回复 """

    TYPE_ARTICLE = "article"
    TYPE_TEXT = "text"
    TYPE_MUSIC = "music"
    TYPE_CHOICES = (
        (TYPE_ARTICLE, '文章'),
        (TYPE_TEXT, '文本'),
        (TYPE_MUSIC, '音乐'),
    )

    keyword = db.XListField(db.StringField(), verbose_name='关键字')
    type = db.StringField(default=TYPE_TEXT, verbose_name='类型', choices=TYPE_CHOICES)
    content = db.StringField(verbose_name='文本回复')
    music = db.EmbeddedDocumentField((MusicItem), verbose_name='音乐')
    article = db.XListField(db.EmbeddedDocumentField(ArticleItem), verbose_name='文章')
    default = db.BooleanField(default=False, verbose_name='默认回复')
    follow = db.BooleanField(default=False, verbose_name='关注回复')
    enable = db.StringField(default=Enable.ENABLED, verbose_name='状态', choices=Enable.CHOICES)
    created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    meta = dict(
        indexes=[
            'id',
            'default',
            'keyword',
        ]
    )

    def reply(self, message, **kwargs):
        if self.type == 'text':
            return TextReply(message=message, content=self.content if self.content else '欢迎关注花胶！')
        elif self.type == 'music':
            if self.music.url:
                return MusicReply(
                    message=message,
                    title=self.music.music_title,
                    description=self.music.music_description,
                    url=self.music.url.link,
                    hq_url=self.music.hq_url.link
                )
        elif self.type == 'article':
            reply = ArticlesReply(message=message)
            if self.article:
                for art in self.article:
                    article = Article(
                        title=art.title,
                        description=art.description,
                        img=art.img.get_link(),
                        url=art.url,
                    )
                    reply.add_article(article)
                return reply
        return ''
