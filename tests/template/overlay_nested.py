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
    <xnode tdi="a"></xnode>
</node>
""".lstrip()).overlay(html.from_string("""
<anode tdi="grumpf" tdi:overlay="foo">
    <bnode tdi="gna" tdi:overlay="bar"></bnode>
</anode>
<anode tdi="zonk" tdi:overlay="bar">
    <bnode tdi="schnick"></bnode>
</anode>
""".lstrip()))

class Model(object):
    def render_nested(self, node):
        node['been'] = u'here'

    def render_gna(self, node):
        node.content = u"whoa!"

    def render_schnick(self, node):
        node.content = u"something"

model = Model()
template.render(model)
