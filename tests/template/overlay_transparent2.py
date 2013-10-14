#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<node tdi="item">
    <znode tdi:overlay="foo">
        <anode tdi:overlay="bar">
            <ynode tdi="subnested"></ynode>
        </anode>
    </znode>
</node>
""".lstrip())

class Model(object):
    def render_item(self, node):
        try:
            node.subnested.content = u"yeah."
        except AttributeError:
            pass

model = Model()
template.render(model)
