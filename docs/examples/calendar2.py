#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import os
os.chdir(os.path.dirname(os.path.abspath(os.path.normpath(__file__))))

import datetime as _dt

from tdi import filters as _filters
from tdi import html as _html
from tdi.tools import html as _html_tools

# We use the same input files like calendar.py on purpose,
# which is to produce the same output under all circumstances.
#
# So, we use the filtering feature to add a tdi attribute to
# the table start tag, which is needed to address the table for
# partial rendering (startnode='table' in the render call).
#
# Also this is a good small example for writing filters.
#
class TableFilter(_filters.BaseEventFilter):
    def handle_starttag(self, name, attr, closed, data):
        if name == 'table':
            attr.append(('tdi', 'table'))
            data = self.builder.encoder.starttag(name, attr, closed)
        self.builder.handle_starttag(name, attr, closed, data)

_html = _html.replace(eventfilters=[TableFilter])


class Model(object):
    def __init__(self, year, month):
        self.first = start = _dt.date(year, month, 1)
        self.end = (start + _dt.timedelta(31)).replace(day=1)
        self.year = year
        self.start = start - _dt.timedelta(start.weekday())
        self.today = _dt.date.today()

    def render_row(self, node):
        weeks, rest = divmod((self.end - self.start).days, 7)
        weeks += bool(rest)
        # repeat over each displayed week (each monday)
        node.repeat(None, (self.start + _dt.timedelta(week * 7)
            for week in xrange(weeks)
        ))

    def render_col(self, node):
        monday = node.ctx[1]
        # repeat over each weekday
        node.repeat(self.repeat_col, (monday + _dt.timedelta(day)
            for day in xrange(7)
        ))

    def repeat_col(self, node, date):
        node.content = date.day
        if date.weekday() >= 5:
            _html_tools.class_add(node, u'weekend')
        if not(self.first <= date < self.end):
            _html_tools.class_add(node, u'fill')
        if date == self.today:
            _html_tools.class_add(node, u'today')

    def separate_col(self, node):
        if node.ctx[0] != 3:
            node.remove()


tpl = _html.from_files(['layout.html', 'calendar.html'])
tpl.render(Model(2014, 1), startnode='table')
