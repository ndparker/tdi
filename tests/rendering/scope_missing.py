#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import ModelMissingError
from tdi import html
from tdi.model_adapters import RenderAdapter

template = html.from_string("""
<node tdi:scope="foo" tdi="nested">
    <xnode tdi="a"></xnode>
</node>
""".lstrip())

class Model(object):

    def render_a(self, node):
        node.content = u'hey'

class DevNull(object):
    def write(self, s):
        pass

model = Model()
def adapter(model):
    return RenderAdapter(model, requirescopes=True)
try:
    template.render(model, stream=DevNull(), adapter=adapter)
except ModelMissingError, e:
    print "OK - ModelMissingError raised: %s" % str(e)
else:
    print "ERROR - ModelMissingError not raised."
