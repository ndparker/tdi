#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html
from tdi.model_adapters import PreRenderWrapper, RenderAdapter

template = html.from_string("""
<foo>
    <bar tdi:overlay=">-foo"/>
</foo>
""".lstrip()).overlay(html.from_string("""
<tdi tdi:overlay="-foo">
    <script tdi="test">JAVASCRIPT</script>
</tdi>
""".lstrip()))

class Model(object):
    def render_test(self, node):
        node.raw.content = node.raw.content.replace('SCR', ' hey ')

def adapter(model):
    return PreRenderWrapper(RenderAdapter(model))

model = Model()
html.from_string(template.render_string(None, adapter=adapter)).render(
    model, startnode="test"
)
print
