#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.model_adapters import RenderAdapter
from tdi import html

template = html.from_string("""
<anode tdi="level1">
    <node tdi="-nested">
        <xnode tdi="a"></xnode>
    </node>
    <ynode tdi="-:nested">lalala</ynode>
</anode>
""".lstrip())

class Model(object):
    def render_nested(self, node):
        node.repeat(self.repeat_nested, (1, 2))

    def repeat_nested(self, node, item):
        pass


model = Model()
template.render(model, adapter=RenderAdapter.for_prerender)
