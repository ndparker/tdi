#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html

template = html.from_string("""
<x tdi="xnode">
    <y tdi="ynode">
        <z tdi="znode">
        </z>
    </y>
</x>
<a tdi=":xnode">
    <b tdi="bnode">
    </b>
</a>
""".lstrip())

class Model(object):

    def render_xnode(self, node):
        node.repeat(None, u"abc")

    def render_znode(self, node):
        node.content = node.ctx[1]

    def render_bnode(self, node):
        node.content = u', '.join(node.ctx[1])


template.render(prerender=Model())
