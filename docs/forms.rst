.. _forms:

表单扩展
========

表单模块主要扩展了一下字段，如验证码、UEditor、WangEditor、以及更方便
使用Bootstrap而重写的一些表单字段。另外，对自动验证支持了中文更本地化的
修改，自动清楚空格。还有，对于mongoengine后台管理更好支持，而重写了表单
基类。

表单基类
--------

主要有 :class:`~chiki.forms.BaseForm` 及支持csrf_token的
:class:`~chiki.forms.Form` 。用法和WTForms及Flask-WTF一致::

    from chiki import Form
    from wtforms.field import TextField

    class TestForm(Form):
        name = TextField('名称')

字段扩展
--------

字段扩展主要有: 
    - 图片验证码: :class:`~chiki.forms.VerifyCodeField`
    - WangEditor: :class:`~chiki.forms.WangEditorField`
    - 其他的类请看 `chiki.forms.fields`

自动验证
--------

自动验证主要有:
    - 清除空格: :class:`~chiki.forms.Strip`
    - 转为小写: :class:`~chiki.forms.Lower`
    - 转为大写: :class:`~chiki.forms.Upper`
    - 限制长度: :class:`~chiki.forms.Length`
    - 要求必填: :class:`~chiki.forms.DataRequired`
