#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item">
    <node tdi="nested">
        <node tdi="subnested"></node>
    </node><tdi tdi=":-nested">
    </tdi>
</node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        for subnode, item in node.nested.iterate([1, 2, 3, 4]):
            subnode['j'] = item
            subnode.content = u'should be here %s' % item
            if item == 3:
                break

model = Model()
template.render(model)
