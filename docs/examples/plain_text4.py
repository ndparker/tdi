#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import text
template = text.from_string(r"""
Hello [[name]]!
""".strip())

class Model(object):
    def render_name(self, node):
        node.content = u"Andr\xe9"

template.render(Model())
print
