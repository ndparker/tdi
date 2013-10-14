#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html
template = html.from_string("""
<html>
<body>
    <ul>
        <li tdi="menu"><a tdi="link">some menu item</a></li>
    </ul>
</body>
</html>
""")

class Model(object):
    def __init__(self, menu, page):
        self._menu = menu
        self._page = page

    # BEGIN INCLUDE
    def render_menu(self, node):
        node.repeat(self.repeat_menu, self._menu)

    def repeat_menu(self, node, (href, menuitem)):
        node.link.content = menuitem
        if (node.ctx[0] + 1 == self._page):
            node.link.hiddenelement = True
        else:
            node.link['href'] = href
    # END INCLUDE

menu = [
    (u'/some/', u'Some Menu Item'),
    (u'/other/', u'Editing Content & Attributes'),
    (u'/third.html', u'Another Menu Item'),
]
model = Model(menu=menu, page=2)
template.render(model)
