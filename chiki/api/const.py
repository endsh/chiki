# coding: utf-8
from __future__ import unicode_literals
from flask.ext.restful import abort as _abort

_code = 0
def code(n=None):
    if not n or type(n) != int:
        n = _code + 1
    globals()['_code'] = n
    return n


_keys = {}
_msgs = {}
def M(**kwargs):
    for key, n in kwargs.iteritems():
        globals()[key] = code(n)
        _keys[globals()[key]] = key
        _msgs[globals()[key]] = key if type(n) == int else n


def abort(code, **kwargs):
    _abort(400, code=code, key=_keys[code], msg=_msgs[code], **kwargs)


M(COMMON_START=20000)
M(SERVER_ERROR='系统出错')
M(ACCESS_DENIED='非法操作')
M(ARGS_ERROR='参数错误')
M(RESOURCE_NOT_FOUND='资源不存在或已被删除')
M(WXAUTH_REQUIRED='请求微信授权登录')
M(WXAUTH_ERROR='微信登录失败')
M(LOGIN_REQUIRED='请先登录')

# 手机验证
M(PHONE_CODE_NOT_NULL='手机验证码不能为空')
M(PHONE_CODE_ERROR='手机验证码不正确')
M(PHONE_CODE_TIMEOUT='手机验证码已失效')
M(PHONE_CODE_TIME_LIMIT='操作太过频繁，请稍候重试')
M(PHONE_NOT_NULL='手机号码不能为空')
M(PHONE_REGISTERED='该手机号码已经被使用')
M(PHONE_UNREGISTERED='该手机号码还没有被绑定')
M(PHONE_FORMAT_ERROR='手机号码格式不正确')
M(PHONE_EXISTS='该手机号码已经被注册')

# 邮箱验证
M(EMAIL_CODE_NOT_NULL='邮箱验证码不能为空')
M(EMAIL_CODE_ERROR='邮箱验证码不正确')
M(EMAIL_CODE_TIMEOUT='邮箱验证码已失效')
M(EMAIL_CODE_TIME_LIMIT='操作太过频繁，请稍候重试')
M(EMAIL_NOT_NULL='邮箱地址不能为空')
M(EMAIL_REGISTERED='该邮箱地址已经被使用')
M(EMAIL_UNREGISTERED='该邮箱地址还没有被绑定')
M(EMAIL_FORMAT_ERROR='邮箱地址格式不正确')
M(EMAIL_EXISTS='该邮箱已经被注册')

# 密码验证
M(PASSWORD_NOT_NULL='密码不能为空')
M(PASSWORD_LENGTH_LIMIT='密码长度必须在6～18个字符之间')
M(PASSWORD_ERROR='密码不正确')

# 帐号验证
M(ACCOUNT_NOT_EXISTS='帐号不存在')
M(ACCOUNT_NOT_NULL='帐号不能为空')
M(ACCOUNT_LOCKED='该帐号已经被锁定，请稍候尝试')

# 其他
M(NOT_ALLOW_BIND='暂时不支持绑定')
M(BINDED='帐号已绑定')
M(NEED_BIND='请先绑定帐号')
M(USER_NICKNAME_EXISTS='该昵称已经被使用')
M(FILE_FORMAT_NOT_SUPPORT='不支持该文件格式')
M(FILE_SIZE_LIMIT='上传的文件过大')
M(USER_SEX_ERROR='无效的性别值')
M(VERIFY_CODE_ERROR='验证码不正确')
