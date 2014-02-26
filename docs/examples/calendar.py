#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import os
os.chdir(os.path.dirname(os.path.abspath(os.path.normpath(__file__))))

# BEGIN INCLUDE
import datetime as _dt

from tdi import html as _html
from tdi.tools import html as _html_tools


class Model(object):
    MONTHS = u"""
        Januar Februar M\xe4rz April Mai Juni Juli August September Oktober
        November Dezember
    """.split()

    def __init__(self, year, month):
        self.first = start = _dt.date(year, month, 1)
        self.end = (start + _dt.timedelta(31)).replace(day=1)
        self.name = self.MONTHS[month - 1]
        self.year = year
        self.start = start - _dt.timedelta(start.weekday())
        self.today = _dt.date.today()

    def render_title(self, node):
        node.content = u"%s %04d" % (self.name, self.year)

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
tpl.render(Model(2014, 1))
