#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<anode tdi="level1">
    <node tdi="*level2">
        <node tdi="level3">
            hey.
        </node>
    </node>
</anode>
""".lstrip())

class Model(object):
    def render_level2(self, node):
        node['foo'] = 'bar'

    def render_level3(self, node):
        node.content = 'sup.'

model = Model()
template.render(model)
