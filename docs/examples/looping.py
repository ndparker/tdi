#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
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

    def render_menu(self, node):
        items = enumerate(node.iterate(self._menu))
        for idx, (subnode, (href, menuitem)) in items:
            subnode.link.content = menuitem
            if (idx + 1 == self._page):
                subnode.link.hiddenelement = True
            else:
                subnode.link['href'] = href

menu = [
    (u'/some/', u'Some Menu Item'),
    (u'/other/', u'Editing Content & Attributes'),
    (u'/third.html', u'Another Menu Item'),
]
model = Model(menu=menu, page=2)
template.render(model)
