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
    <xnode tdi="a"></xnode>
</node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        for subnode, item in node.nested.iterate([]):
            subnode['j'] = item
            subnode.content = u'should be here %s' % item
        return True

    def render_a(self, node):
        node.content = u"should not be here"

model = Model()
template.render(model)
