# coding: utf-8
import os
import time
import hashlib


class BaseGenerator(object):

    def __init__(self, local=False):
        self.local = local


class RandomGenerator(BaseGenerator):

    def __call__(self):
        md5 = hashlib.md5(os.urandom(32).encode('hex')).hexdigest()
        if self.local:
            return '%s/%s/%s' % (md5[:2], md5[2:4], md5[4:])
        return md5


class DatetimeGenerator(BaseGenerator):
    """ 多进程下会有Bug """

    def __init__(self, local=False):
        self.local = local
        self.tpl = '%Y%m%d/%H%M%S' if self.local else '%Y%m%d%H%M%S'

    stamp = long(time.time())
    index = 0

    @staticmethod
    def get_index():
        if long(time.time()) > DatetimeGenerator.stamp:
            DatetimeGenerator.stamp = time.time()
            DatetimeGenerator.index = 0
        DatetimeGenerator.index += 1
        return DatetimeGenerator.index

    def __call__(self):
        return '%s%02d' % (time.strftime(self.tpl), DatetimeGenerator.get_index())