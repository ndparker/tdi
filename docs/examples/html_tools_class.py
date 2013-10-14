#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html as html_template
from tdi.tools import html

tpl = html_template.from_string("""
<div tdi="div1" class="open">Container 1</div>
<div tdi="div2">Container 2</div>
""".lstrip())

class Model(object):
    def render_div1(self, node):
        html.class_del(node, u'open')

    def render_div2(self, node):
        html.class_add(node, u'open', u'highlight')

tpl.render(Model())
