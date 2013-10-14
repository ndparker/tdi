#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import text
template = text.from_string("""
[? encoding = cp1252 ?]Hello [[name]]!

Euro Sign: [[euro]]
""".strip())

class Model(object):
    def render_name(self, node):
        node.content = u"Andr\xe9"

    def render_euro(self, node):
        node.content = u"\u20ac"

print repr(template.render_string(Model()))
