# coding: utf-8
import time
import functools
import inspect
from chiki.contrib.common.models import StatLog
from datetime import datetime, timedelta
from flask import request
from flask.ext.admin import expose
from flask.ext.admin.base import _wrap_view
from .utils import json_success


def get_date_ranger(date_start, date_end):
    #
    dates = []
    start = datetime.strptime(date_start, '%Y-%m-%d')
    end = datetime.strptime(date_end, '%Y-%m-%d')
    size = (end - start).days

    if size >= 0:
        i = 0
        while i < size + 1:
            dates.append((start + timedelta(days=i)).strftime('%Y-%m-%d'))
            i += 1
    return dates


def get_date(key='day'):
    #
    day = request.args.get(key, '')
    try:
        datetime.strptime(day, '%Y-%m-%d')
    except ValueError:
        day = time.strftime('%Y-%m-%d')
    return day


def get_dates(stat=True, start_key='start', end_key='end', start='', end=''):
    #
    if callable(start):
        start = start()
    if callable(end):
        end = end()

    start = request.args.get(start_key, start)
    end = request.args.get(end_key, end)

    try:
        datetime.strptime(start, '%Y-%m-%d')
        datetime.strptime(end, '%Y-%m-%d')
    except (ValueError, TypeError):
        start = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')

    if stat is True:
        days = get_date_ranger(start, end)
        if len(days) == 0:
            start = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
            end = datetime.now().strftime('%Y-%m-%d')

    return start, end


def get_value_list(key, days, tid=None):
    #
    query = dict(key=key, day__in=days)
    if tid:
        query['tid'] = tid

    length = len(days)
    value_list = [0 for i in range(length)]
    items = StatLog.objects(**query)
    for item in items:
        value_list[days.index(item.day)] = item.value
    return value_list


def get_hour_list(key, day, tid=None, hour=23):
    #
    query = dict(key=key, day=day)
    if tid:
        query['tid'] = tid

    items = StatLog.objects(**query)
    values = [0 for i in range(hour + 1)]
    for item in items:
        if item.hour <= hour:
            values[item.hour] = item.value
    return values


def hour_value_list(day, key, *args, **kwargs):
    #
    return get_hour_list(key, day, **kwargs)


# 获得比值
def get_value(value, value2, default=True):
    if value == 0:
        return 0
    if value2 == 0 or not value2:
        result = value * 100.0 / abs(value)
    else:
        result = value * 100.0 / value2

    if result < -20 and default:
        return -20
    elif result > 120 and default:
        return 120
    return result


# 多个值打包成一个
#
def get_sum_value(data):
    values = zip
    for v in data:
        values = functools.partial(values, v)
    return list(map(lambda x: sum(x), values()))


# 获取一个key的值 或多个key 的和
#
def date_value(key, days):
    if isinstance(key, list):
        value_list = [get_value_list('date_%s' % x, days) for x in key]
        return get_sum_value(value_list)
    return get_value_list('date_%s' % key, days)


# 获取一个key的值 或多个key 的和
#
def hour_value(key, day):
    if isinstance(key, list):
        value_list = [get_hour_list('hour_%s' % x, day) for x in key]
        return get_sum_value(value_list)
    return get_hour_list('hour_%s' % key, day)


# 获取 key, key2, type
#
def change_value_list(data, key, days):
    style = data.get('style', '/')
    key_data = date_value(data.get('key'), days)
    key2_data = date_value(data.get('key2'), days)
    if style == '+':
        return list(map(lambda x: x[0] + x[1], zip(key_data, key2_data)))
    if style == '-':
        return list(map(lambda x: x[0] - x[1], zip(key_data, key2_data)))
    return list(map(lambda x: get_value(x[0], x[1], data.get('default', True)), zip(key_data, key2_data)))


# 获取 key, key2, type
#
def hour_change_value_list(data, day, key, *args, **kwargs):
    style = data.get('style', '/')
    key_data = hour_value(data.get('key'), day)
    key2_data = hour_value(data.get('key2'), day)
    if style == '+':
        return list(map(lambda x: x[0] + x[1], zip(key_data, key2_data)))
    if style == '-':
        return list(map(lambda x: x[0] - x[1], zip(key_data, key2_data)))
    return list(map(lambda x: get_value(x[0], x[1], data.get('default', True)), zip(key_data, key2_data)))


def init_stat(cls, key, subs, tpl, projects, modal, **kwargs):
    """ 初始化统计 """

    @expose('/' if key == 'index' else '/%s' % key)
    def index(self):
        now = datetime.now()
        start, end = get_dates(stat=True, start=kwargs.get('start'), end=kwargs.get('end'))
        month_start = kwargs.get('month_start', (now - timedelta(days=30)).strftime('%Y-%m-%d'))
        week_start = kwargs.get('week_start', (now - timedelta(days=6)).strftime('%Y-%m-%d'))
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        today = now.strftime('%Y-%m-%d')
        data_url = self.get_url('.%s_data' % key)
        if modal:
            data_url = self.get_url('.%s_data' % key, id=request.args.get('id'))
        return self.render(
            tpl,
            start=start, end=end, month_start=month_start, month_end=today,
            week_start=week_start, week_end=today, yesterday=yesterday,
            today=today, data_url=data_url, model=kwargs.get('model', 'day'))

    def get_series(sub, day, prefix, axis, value_list, id=None):
        res = []
        series = sub.get('series')
        if callable(series):
            if 'day' in inspect.getargspec(series)[0]:
                series = series(day=day)
            else:
                series = series()
        for item in series:
            if 'hour_value_list' in item and prefix == 'hour_':
                value_list = item.get('hour_value_list')
                value_list = functools.partial(value_list, day)
            elif 'value_list' in item and prefix == 'date_':
                value_list = item.get('value_list')

            # change 的格式: dict(key=*, key2=*, type='rate') 或 方法
            if 'change' in item:
                change_date = item.get('change')
                if callable(change_date):
                    value_list = functools.partial(change_date, prefix, day)

                if isinstance(change_date, dict):
                    if prefix == 'hour_':
                        value_list = functools.partial(hour_change_value_list, change_date, day)
                    elif prefix == 'date_':
                        value_list = functools.partial(change_value_list, change_date)
            key = '%s%s' % (prefix, item.get('key'))
            if modal:
                key = '%s_%s' % (key, id or request.args.get('id'))
            if projects:
                # if set(['value_list', 'change']).intersection(item):
                if 'hour_value_list' in item and prefix == 'hour_':
                    value = value_list(key, projects)
                elif 'value_list' in item and prefix == 'date_':
                    value = value_list(key, axis, projects)
                else:
                    value = value_list(key, axis)
            else:
                # axis： 小时列表或者天列表
                value = value_list(key, axis)
            handle = item.get('handle')
            if callable(handle):
                value = [handle(x) for x in value]
            res.append(dict(name=item.get('name'), data=value))
        return res

    def common_data(prefix, subtitle, axis, value_list, id=None):
        items = []
        day = subtitle
        subtitle += '<br>'
        for sub in subs:
            item = dict(
                title=sub.get('title'),
                suffix=sub.get('suffix'),
                axis=axis,
                series=get_series(sub, day, prefix, axis, value_list, id=id),
            )
            totals = []
            tpl = '<span>%s: %d%s</span>'
            for ser in item['series']:
                totals.append(tpl % (ser['name'], sum(ser['data']), sub.get('suffix')))
            item['subtitle'] = subtitle + ' - '.join(totals)
            items.append(item)
        return json_success(items=items)

    def hour_data(id=None):
        day = get_date()
        hours = ['%02d时' % i for i in range(24)]
        value_list = functools.partial(hour_value_list, day)
        return common_data('hour_', day, hours, value_list, id=id)

    def date_data(id=None):
        start, end = get_dates(True)
        days = get_date_ranger(start, end)
        return common_data('date_', '%s 至 %s' % (start, end), days, get_value_list, id=id)

    @expose('/data' if key == 'index' else '/%s/data' % key)
    def data(self):
        model = request.args.get('model', 'day')
        if model == 'day':
            return date_data()
        return hour_data()

    def simple(self, id):
        model = request.args.get('model', 'day')
        if model == 'day':
            return date_data(id)
        return hour_data(id)

    setattr(cls, key, index)
    setattr(cls, '%s_data' % key, data)
    setattr(cls, '%s_data_simple' % key, simple)


def statistics(tpl=None, modal=False, projects=None, **kwargs):
    def wrapper(cls):
        default = 'admin/stat-modal.html' if modal else 'admin/stat.html'
        datas = getattr(cls, 'datas', None)
        # data = getattr(cls, 'data', None)
        if datas:
            for key, subs in datas.iteritems():
                init_stat(cls, key, subs, tpl if tpl is not None else default, projects, modal)
        # if data:
        #     for key, subs in data.iteritems():
        #         init_stat(cls, key, subs, tpl if tpl is not None else default, projects, modal)
        for p in dir(cls):
            attr = getattr(cls, p)
            if hasattr(attr, '_urls'):
                for url, methods in attr._urls:
                    cls._urls.append((url, p, methods))
                    if url == '/':
                        cls._default_view = p
                setattr(cls, p, _wrap_view(attr))
        return cls
    return wrapper


class Stat(object):
    """ 统计助手 """

    def __init__(self):
        self.items = []
        self.funcs = []
        self.start = datetime(2016, 1, 1)
        self.minutes = 1

    def _save(self, _key, _day, _hour, _value, **kwargs):
        if callable(_value):
            _value = _value(**kwargs)

        if type(_value) is list:
            for item in _value:
                if type(item['value']) == dict:
                    for sk, sv in item['value'].iteritems():
                        if type(sv) == dict:
                            for xk, xv in sv.iteritems():
                                query = dict(key=_key.format(_id=item['_id'], key=sk, skey=xk),
                                     day=_day, hour=_hour)
                                StatLog.objects(**query).update(
                                    set__value=xv,
                                    set__modified=datetime.now(),
                                    set_on_insert__created=datetime.now(),
                                    upsert=True,
                                )
                        else:
                            query = dict(key=_key.format(_id=item['_id'], key=sk),
                                         day=_day, hour=_hour)
                            StatLog.objects(**query).update(
                                set__value=sv,
                                set__modified=datetime.now(),
                                set_on_insert__created=datetime.now(),
                                upsert=True,
                            )
                else:
                    StatLog.objects(key=_key.format(**item), day=_day, hour=_hour).update(
                        set__value=item['value'],
                        set__modified=datetime.now(),
                        set_on_insert__created=datetime.now(),
                        upsert=True,
                    )
        else:
            StatLog.objects(key=_key, day=_day, hour=_hour).update(
                set__value=_value,
                set__modified=datetime.now(),
                set_on_insert__created=datetime.now(),
                upsert=True,
            )

    def save(self, _key, _day, _start, _end, _value, _hour=0, field='created', **kwargs):
        if field is not None:
            kwargs.setdefault('%s__gte' % field, _start)
            kwargs.setdefault('%s__lt' % field, _end)
        return self._save(_key, _day, _hour, _value=_value, **kwargs)

    def stat(self, _key, _model, _query=lambda x: x.count(), _handle=lambda x: x, mode='all', **kwargs):
        self.items.append(dict(
            key=_key,
            model=_model,
            query=_query,
            handle=_handle,
            kwargs=kwargs,
            mode=mode,
        ))

    def count(self, _key, _model, **kwargs):
        return self.stat(_key, _model, **kwargs)

    def sum(self, _key, _model, _sub, **kwargs):
        return self.stat(_key, _model, _query=lambda x: x.aggregate_sum(_sub), **kwargs)

    def distinct(self, _key, _model, _sub, **kwargs):
        return self.stat(_key, _model, _query=lambda x: x.distinct(_sub), _handle=len, **kwargs)

    def aggregate(self, _key, _model, *pipline, **kwargs):
        return self.stat(_key, _model, _query=lambda x: list(x.aggregate(*pipline)), **kwargs)

    def aggregate2(self, _key, _model, _model2, _sub, *pipline, **kwargs):
        handle = lambda x: list(_model.objects(id__in=x).aggregate(*pipline))
        query = lambda x: x.distinct(_sub)
        return self.stat(_key, _model2, _query=query, _handle=handle, **kwargs)

    def func(self, f):
        self.funcs.append(f)
        return f

    def one(self, key, day, start, end, hour=0):
        for item in self.items:
            if item['mode'] == 'all' or key == item['mode']:
                value = lambda **x: item['handle'](item['query'](item['model'].objects(**x)))
                self.save('%s_%s' % (key, item['key']), day, start, end, value, hour, **item['kwargs'])
        for f in self.funcs:
            f(key, day, start, end, hour)

    def day(self, day):
        self.time_start = start = datetime.strptime(str(day).split(' ')[0], '%Y-%m-%d')
        self.time_end = end = datetime.strptime(str(day + timedelta(days=1)).split(' ')[0], '%Y-%m-%d')
        self.one('date', day.strftime('%Y-%m-%d'), start, end)

    def hour(self, now, day=True):
        start = now - timedelta(minutes=self.minutes)
        self.time_start = start = start - timedelta(minutes=start.minute, seconds=start.second, microseconds=start.microsecond)
        self.time_end = end = start + timedelta(hours=1)
        self.now = start
        self.one('hour', start.strftime('%Y-%m-%d'), start, end, hour=start.hour)
        if day:
            self.day(start)

    def all(self):
        now = datetime.now()
        while now >= self.start:
            print 'stat:', now
            self.hour(now, day=now.hour == 0)
            now -= timedelta(hours=1)

    def run(self, start=datetime(2016, 1, 1), minutes=1):
        self.start = start
        self.minutes = minutes

        def run_stat(model='last'):
            if model in ['last', 'simple']:
                start = time.time()
                print 'stat hour:', datetime.now(),
                self.hour(datetime.now())
                print time.time() - start
            elif model == 'all':
                self.all()

        return run_stat
