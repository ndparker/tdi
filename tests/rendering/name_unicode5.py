#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node>
    <xnode tdi="foo"></xnode>
</node>
""".lstrip())

class Model(object):
    def render_foo(self, node):
        try:
            node[u'b\xe9lah'] = u'bl\xf6d'
        except UnicodeError:
            node[u'blah'] = u'bl\xf6d'

template.render(Model())
