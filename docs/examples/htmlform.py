#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
from tdi.tools import htmlform
template = html.from_string("""
<html>
<body>
    <p>Type your name:</p>
    <form tdi="form">
        <input tdi="name" type="text" />
        <input tdi="submit" type="submit" />
    </form>
</body>
</html>
""")

class Model(object):
    def __init__(self):
        self._form = htmlform.HTMLForm()

    def render_form(self, node):
        self._form.form(node)

    def render_name(self, node):
        self._form.text(node, u"name")

    def render_submit(self, node):
        self._form.submit(node, u"send", u"Submit form")

model = Model()
template.render(model)
