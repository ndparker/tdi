#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item">
    <znode tdi="nested" tdi:overlay="foo">
        <ynode tdi="subnested"></ynode>
    </znode>
    <xnode tdi=":nested" tdi:overlay="bar"> separator </xnode>
</node>
""".lstrip()).overlay(html.from_string("""
<anode tdi:overlay="foo" tdi="zonk"> overlayed </anode>
<bnode tdi=":zonk"> zonked </bnode>
""".lstrip()))

class Model(object):
    def render_nested(self, node):
        for subnode, item in node.iterate([0, 1]):
            subnode.content = item

model = Model()
template.render(model)
