#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.model_adapters import RenderAdapter
from tdi import html

template = html.from_string("""
<anode tdi="anode"></anode>
""".lstrip())

class Model(object):
    def __init__(self, version):
        self._version = version

    def prerender_version(self, version):
        return version != self._version, self._version

    def render_anode(self, node):
        print "render_anode", self._version


print template.render_string(prerender=Model(1))
print "---"
print template.render_string(prerender=Model(1))
print "---"
print template.render_string(prerender=Model(2))
print "---"
print template.render_string(prerender=Model(2))
