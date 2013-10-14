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
        for subnode, item in node.iterate([1, 2, 3, 4]):
            xitem = subnode.xitem
            xitem.replace(None, xitem.yitem)
            xitem.a.content = item

model = Model()
template.render(model)
