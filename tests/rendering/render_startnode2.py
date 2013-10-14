#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<anode tdi="level1">
    <node tdi="nested">
        <xnode tdi="a"></xnode>
    </node>
</anode>
""".lstrip())

class Model(object):

    def render_a(self, node):
        node.content = u'hey'

model = Model()
template.render(model, startnode='nested.a')
print
