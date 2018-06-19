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
        title=formatter_popover(lambda m: (m.title, text2html(m.content)), max_len=60),
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
