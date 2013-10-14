#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.model_adapters import RenderAdapter
from tdi import html

template = html.from_string("""
<anode tdi="level1" tdi:prerender="remove-node">
    <node tdi="-nested">
        <xnode tdi="a">
            <znode tdi="b">foo</znode>
        </xnode>
    </node>
    <ynode tdi="-:nested">lalala</ynode>
</anode>
""".lstrip())

class Model(object):
    def render_a(self, node):
        node.b.content = u'hey'
        node.b.hiddenelement = True
        node.b['tdi:prerender'] = u'remove-node'

model = Model()
template.render(model, adapter=RenderAdapter.for_prerender)
