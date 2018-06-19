# coding: utf-8
from chiki.stat import get_dates
from chiki.forms import Form
from chiki.contrib.users import um
from wtforms import PasswordField
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for
from flask.ext.login import current_user, login_user, login_required
from .admin import ChannelView
from .models import Channel

bp = Blueprint('outer', __name__)


class LoginForm(Form):
    password = PasswordField('密码')

    def validate_password(self, field):
        if self.user.password != self.password.data:
            raise ValueError('密码不正确')


@bp.route('/login/<int:id>', methods=['GET', 'POST'])
def login(id):
    user = Channel.objects(id=id).get_or_404()
    form = LoginForm()
    form.user = user
    if form.validate_on_submit():
        login_user(user)
        return redirect(url_for('outer.index'))
    return render_template('outer/login.html', form=form, user=user)


@bp.route('/')
@login_required
def index():
    now = datetime.now()
    start, end = get_dates(stat=True)
    month_start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    week_start = (now - timedelta(days=6)).strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    today = now.strftime('%Y-%m-%d')
    return render_template('outer/index.html',
        start=start,
        end=end,
        month_start=month_start,
        month_end=today,
        week_start=week_start,
        week_end=today,
        yesterday=yesterday,
        today=today,
    )


view = ChannelView(Channel)


@bp.route('/data')
@login_required
def data():
    channel = Channel.objects(id=current_user.id).get_or_404()
    return view.stat_data_simple(channel.id)
