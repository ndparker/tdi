#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import os
os.chdir(os.path.dirname(os.path.abspath(os.path.normpath(__file__))))

# BEGIN INCLUDE
from tdi import html

class Model(object):
    def __init__(self, name, table):
        self.name = name
        self.table = table

    def render_title(self, node):
        node.content = self.name

    def render_row(self, node):
        node.repeat(None, self.table)

    def render_col(self, node):
        cols = node.ctx[1]
        node.repeat(self.repeat_col, cols)

    def repeat_col(self, node, col):
        node.content = col

table = [
    ( 1,  2,  3,   4,   5,   6,   7),
    ( 8,  9, 10,  11,  12,  13,  14),
    (15, 16, 17,  18,  19,  20,  21),
    (22, 23, 24,  25,  26,  27,  28),
    (29, 30, 31, u'', u'', u'', u''),
]
tpl = html.from_files(['layout.html', 'calendar.html'])
tpl.render(Model(u"M\xe4rz", table))
