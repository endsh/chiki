.. _quickstart:

入门教程
========

一个简单的项目
--------------

在 :ref:`installation` 中基本给出了创建新项目的所有步骤，这里再给出一个完整的例子::

    mkvirtualenv simple
    pip install chiki
    chiki https://github.com/endsh/cookiecutter-chiki.git -a -w
    cd simple

这样新项目就创建完成了，项目结构介绍请看 :ref:`projection`，运行以下命令就可以启动服务器了::

    python manage.py admin -d -r  // 后台管理服务器
    python manage.py api -d -r    // 移动接口(rest)服务器
    python manage.py web -d -r    // 网站服务器

这个例子放在 `examples/simple`_ , 现在创建文件 `simple/index.py`_::
    
    # coding: utf-8
    from flask import Blueprint

    bp = Blueprint('index', __name__)

    @bp.route('/')
    def index():
        return 'hello chiki.'

在文件 `simple/web.py` 添加以下代码::

    from simple import index

    def init_routes(app):
        app.register_blueprint(index.bp)

打开地址 http://0.0.0.0:5002/ 即可看到: hello chiki.

实现简单博客
------------

创建文件 `simple/articles.py`_ 实现文章建模，后台管理视图，以及文章增删改查，
为简单一点，这里把admin/forms/models/views/__init__几个文件的内容合并在一个文件::

    # coding: utf-8
    from chiki import text2html
    from chiki.admin import formatter_popover, ModelView
    from chiki.forms import Form
    from datetime import datetime
    from flask import Blueprint, render_template, redirect, request, url_for
    from wtforms import TextField, TextAreaField
    from simple.base import db

    class Article(db.Document):
        """ 文章模型 """

        title = db.StringField(max_length=200, verbose_name='标题')
        content = db.StringField(verbose_name='正文')
        modified = db.DateTimeField(default=datetime.now, verbose_name='修改时间')
        created = db.DateTimeField(default=datetime.now, verbose_name='创建时间')

    class ArticleView(ModelView):
        """ 文章管理 """
        show_popover = True
        column_default_sort = '-created'
        column_list = ('title', 'modified', 'created')
        column_center_list = ('modified', 'created')
        column_searchable_list = ('title',)
        column_formatters = dict(
            title=formatter_popover(
                lambda m: (m.title, text2html(m.content)), max_len=60),
        )

    class ArticleForm(Form):
        """ 文章表单 """
        title = TextField('标题')
        content = TextAreaField('正文')


    bp = Blueprint('articles', __name__)

    @bp.route('/')
    def index():
        """ 文章列表 """
        page = max(1, request.args.get('page', 1, int))
        per_page = max(1, min(20, request.args.get('per_page', 10, int)))
        arts = Article.objects.paginate(page=page, per_page=per_page)
        return render_template('articles/index.html', arts=arts)

    @bp.route('/new', methods=['GET', 'POST'])
    def new():
        """ 创建文章 """
        form = ArticleForm()
        if form.validate_on_submit():
            art = Article()
            form.populate_obj(art)
            art.save()
            return redirect(url_for('.detail', id=art.id))
        return render_template('articles/new.html', form=form)

    @bp.route('/<id>')
    def detail(id):
        """ 文章详情 """
        art = Article.objects(id=id).get_or_404()
        return render_template('articles/detail.html', art=art)

    @bp.route('/<id>/edit', methods=['GET', 'POST'])
    def edit(id):
        """ 编辑文章 """
        art = Article.objects(id=id).get_or_404()
        form = ArticleForm(obj=art)
        if form.validate_on_submit():
            form.populate_obj(art)
            art.save()
            return redirect(url_for('.detail', id=id))
        return render_template('articles/new.html', form=form)

在文件 `simple/web.py` 以下代码，注册蓝图::

    from simple import index, articles

    def init_routes(app):
        app.register_blueprint(index.bp)
        app.register_blueprint(articles.bp, url_prefix='/articles')

在文件 `simple/admin/__init__.py` 添加以下代码，支持后台管理::
    
    from simple.articles import Article, ArticleView

    def init(app):
        """ 初始化后台管理 """
        admin.add_view(ArticleView(Article, name='文章'))

还需要添加相应的模版文件，放在 `templates/articles` 目录下。暂时还没支持前端样式，
所以看起来比较难看。

这样，一个简单的博客系统就完成了。可通过 http://0.0.0.0:5002/articles/ 查看文章列表，通过
http://0.0.0.0:5000/admin/ 查看后台管理（帐号: admin 密码为空）

以上用到的很多地方，可能还需要查看后面的文档才能理解，这里暂时只需要能够运行，先给看效果。


.. _examples/simple: https://github.com/endsh/chiki/tree/master/examples/simple
.. _simple/index.py: https://github.com/endsh/chiki/tree/master/examples/simple/simple/index.py
.. _simple/web.py: https://github.com/endsh/chiki/tree/master/examples/simple/simple/web.py
.. _simple/articles.py: https://github.com/endsh/chiki/tree/master/examples/simple/simple/articles.py
.. _simple/admin/__init__.py: https://github.com/endsh/chiki/tree/master/examples/simple/simple/admin/__init__.py
.. _templates/articles: https://github.com/endsh/chiki/tree/master/examples/simple/templates