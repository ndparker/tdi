#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node>
    <xnode tdi="zonk" tdi:scope="foo"></xnode>
</node>
""".lstrip())


class FooModel(object):
    def render_zonk(self, node):
        node.content = u"Yay."


class Model(object):
    def __init__(self):
        self.scope_foo = FooModel()


model = Model()
template.render(model)
