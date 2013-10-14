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
        <div tdi="-name">
            <p tdi="*error" class="error">Error message</p>
            <input tdi="*field" id="name" type="text" />
        </div>
        <input tdi="submit" type="submit" />
    </form>
</body>
</html>
""")

class Model(object):
    def __init__(self, errors=None):
        self._errors = errors or {}
        self._form = htmlform.HTMLForm(
            pre_proc=self.preproc,
            post_proc=htmlform.TabIndexer(),
        )

    def preproc(self, which, node, kwargs):
        """ HTMLForm node pre processor """
        try:
            fieldnode = node.field
        except AttributeError:
            fieldnode = node
        else:
            try:
                errornode = node.error
            except AttributeError:
                pass
            else:
                name = kwargs.get('name')
                if name and name in self._errors:
                    errornode.content = self._errors[name]
                else:
                    errornode.remove()

        return fieldnode, kwargs

    def render_form(self, node):
        self._form.form(node)

    def render_name(self, node):
        self._form.text(node, u"name")

    def render_submit(self, node):
        self._form.submit(node, u"send", u"Submit form")

model = Model(errors=dict(name=u'Please do enter a name!'))
template.render(model)
