#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
template = html.from_string("""
<html>
<body>
    <h1 tdi="doctitle">doc title goes here</h1>
    <p tdi="intro">Intro goes here.</p>
</body>
</html>
""")

class Model(object):
    def render_doctitle(self, node):
        node.content = u"Editing Content & Attributes"

    def render_intro(self, node):
        node.content = u"Modifying content and markup attributes is easy."
        node['class'] = u"edit-intro"

model = Model()
template.render(model)
