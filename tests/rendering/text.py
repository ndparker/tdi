#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import text

template = text.from_string("""
Hello [[name]]!

Look, hey, this is a text []template]. And here's a list:

[item]* some stuff[/item][tdi=":item"]
[/]

Thanks for [[+listening]].
""".lstrip())

class Model(object):
    def render_name(self, node):
        node.content = u"Andr\xe9"

    def render_item(self, node):
        for snode, fruit in node.iterate((u'apple', u'pear', u'cherry')):
            snode.content = u'* %s' % fruit

template.render(Model())
