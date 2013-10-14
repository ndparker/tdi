#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item">
    <znode tdi="nested">
        <ynode tdi="subnested"></ynode>
    </znode>
    <xnode tdi="a"></xnode>
</node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        node.replace(self.replace_nested, node.nested)
        return True

    def replace_nested(self, node):
        node.replace(self.replace_subnested, node.subnested)
        return True

    def replace_subnested(self, node):
        node.content = "yay..."

model = Model()
template.render(model)
