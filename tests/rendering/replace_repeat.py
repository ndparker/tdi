#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item"><xnode tdi="xitem"></xnode></node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        xnode = node.copy()
        def foo(node, item):
            node.content = item
        node.xitem.replace(None, xnode).repeat(foo, (1, 2))


model = Model()
template.render(model)
