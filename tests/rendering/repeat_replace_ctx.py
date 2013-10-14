#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item"><xnode tdi="xitem"><ynode tdi="yitem">
</ynode></xnode></node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        node.repeat(self.repeat_item, [1, 2, 3, 4])

    def repeat_item(self, node, item):
        node.replace(None, node.xitem, 'foo')

    def render_yitem(self, node):
        node.content = repr(node.ctx)

model = Model()
template.render(model)
