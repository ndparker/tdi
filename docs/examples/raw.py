#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
template = html.from_string("""
<div tdi="banner1"></div>
<div tdi="banner2"></div>
""")

class Model(object):
    def render_banner1(self, node):
        node.content = '<p>Banner!</p>'

    def render_banner2(self, node):
        node.raw.content = '<p>Banner!</p>'

template.render(Model())
