#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item">
    <node tdi="nested">
        <node tdi="subnested"></node>
    </node>
    <xnode tdi="a"></xnode>
</node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        node.nested.replace(self.replace_nested, node.a)
        return True

    def replace_nested(self, node):
        node['been'] = u'here'
        node.content = u'yes'

    def render_a(self, node):
        node.content = u"should not be here"

model = Model()
template.render(model)
