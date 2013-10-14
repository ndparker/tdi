#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item"><xnode tdi="xitem"><ynode tdi="yitem">
<a tdi="-a" />
</ynode></xnode></node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        node.xitem.yitem
        node.repeat(None, [1, 2, 3, 4])

    def render_xitem(self, node):
        ctx = node.ctx
        node.replace(None, node.yitem).ctx = ctx

    def render_a(self, node):
        node.content = node.ctx[1]

model = Model()
template.render(model)
