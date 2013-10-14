#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<anode tdi="level1">
</anode><bnode tdi="*:level1">
</bnode>
""".lstrip())

class Model(object):
    def render_level1(self, node):
        def repeat(node, item):
            node.content = item
        node.repeat(repeat, [1, 2, 3])

    def separate_level1(self, node):
        node['foo'] = 'bar'


model = Model()
template.render(model)
