import os
from xml.sax.saxutils import escape
from flask import render_template, current_app
from flask_debugtoolbar.panels import DebugPanel
from chiki.jinja import markup
import pprint
import operation_tracker


def format_stack_trace(value):
    stack_trace = []
    fmt = (
        '<span class="path">{0}/</span>'
        '<span class="file">{1}</span> in <span class="func">{3}</span>'
        '(<span class="lineno">{2}</span>) <span class="code">{4}</span>'
    )
    for frame in value:
        params = map(escape, frame[0].rsplit('/', 1) + list(frame[1:]))
        stack_trace.append(fmt.format(*params))
    return markup('\n'.join(stack_trace))


def embolden_file(path):
    head, tail = os.path.split(escape(path))
    return markup(os.sep.join([head, '<strong>{0}</strong>'.format(tail)]))


def format_dict(value, width=60):
    return pprint.pformat(value, width=int(width))


def highlight(value, language):
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name
        from pygments.formatters import HtmlFormatter
    except ImportError:
        return value
    # Can't use class-based colouring because the debug toolbar's css rules
    # are more specific so take precedence
    formatter = HtmlFormatter(style='friendly', nowrap=True, noclasses=True)
    return highlight(value, get_lexer_by_name(language), formatter)


filters = dict(
    format_stack_trace=format_stack_trace,
    embolden_file=embolden_file,
    format_dict=format_dict,
    highlight=highlight,
)


class MongoDebugPanel(DebugPanel):
    """Panel that shows information about MongoDB operations.
    """
    name = 'MongoDB'
    has_content = True

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        operation_tracker.install_tracker()
        current_app.jinja_env.filters.update(filters)

    def process_request(self, request):
        operation_tracker.reset()

    def nav_title(self):
        return 'MongoDB'

    def nav_subtitle(self):
        num_queries = len(operation_tracker.queries)
        attrs = ['queries', 'inserts', 'updates', 'removes']
        total_time = sum(sum(o['time'] for o in getattr(operation_tracker, a))
                         for a in attrs)
        return '{0} operations in {1:.2f}ms'.format(num_queries, total_time)

    def title(self):
        return 'MongoDB Operations'

    def url(self):
        return ''

    def content(self):
        context = self.context.copy()
        context['queries'] = operation_tracker.queries
        context['inserts'] = operation_tracker.inserts
        context['updates'] = operation_tracker.updates
        context['removes'] = operation_tracker.removes
        context.update(**filters)

        return render_template('mongo-panel.html', **context)
