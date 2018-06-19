# coding: utf8
import sys
import logging
import logging.handlers
import traceback
from StringIO import StringIO
from datetime import datetime
from chiki.contrib.common import Log
from flask import request

reload(sys)

sys.setdefaultencoding('utf8')

__all__ = [
    'Logger', 'init_logger', 'DEBUG_LOG_FORMAT',
]

DEBUG_LOG_FORMAT = (
    '-' * 80 + '\n' +
    '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
    '%(message)s\n' +
    '-' * 80
)


class ChikiHandler(logging.Handler):

    def emit(self, record):
        try:
            exc = ''
            if record.exc_info:
                ei = record.exc_info
                sio = StringIO()
                traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
                exc = sio.getvalue()
                sio.close()

            Log(
                name=record.name,
                levelname=record.levelname,
                thread=record.thread,
                threadName=record.threadName,
                module=record.module,
                funcName=record.funcName,
                lineno=record.lineno,
                message=record.msg,
                exc=exc,
                url=request.url,
                user_agent=request.headers.get('User-Agent', ''),
                created=datetime.fromtimestamp(record.created),
            ).save()
        except:
            traceback.print_exc()


class Logger(object):

    def __init__(self, app=None):
        # logging.basicConfig(
        #     format='%(asctime)s %(message)s',
        #     datefmt='%a, %d %b %Y %H:%M:%S',)
        if app:
            self.init_app(app)

    def init_app(self, app):
        config = app.config.get('LOGGING')
        handler = ChikiHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        if not config:
            return

        # config_mail = config.get('SMTP')
        # if config_mail: #如果存在smtp配置
        #     app.logger.info('Add SMTP Logging Handler')
        #     mail_handler = logging.handlers.SMTPHandler(
        #         config_mail['HOST'],  #smtp 服务器地址
        #         config_mail['USER'], #smtp 发件人
        #         config_mail['TOADDRS'], #smtp 收件人
        #         config_mail['SUBJECT'], #smtp 主题
        #         (config_mail['USER'], config_mail['PASSWORD'])) #smtp账号密码
        #     mail_handler.setLevel(logging.ERROR)
        #     app.logger.addHandler(mail_handler)
        # else:
        #     app.logger.info('No SMTP Config Found')

        config_file = config.get('FILE')
        if config_file:#如果存在文件配置
            app.logger.info('Add File Logging Handler')
            file_handler = logging.handlers.RotatingFileHandler(
                config_file['PATH'],#文件路径
                #但个文件大小 默认10M
                maxBytes=config_file.setdefault('MAX_BYTES', 1024 * 1024 * 10),
                #文件备份>数量 默认5个
                backupCount=config_file.setdefault('BACKUP_COUNT', 5),
            )
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        else:
            app.logger.info('No FILE Config Found')


def init_logger(app):
    logger = Logger()
    logger.init_app(app)
