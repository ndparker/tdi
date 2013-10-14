#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html
template = html.from_string("""
<html>
<body>
    <h1 tdi="doctitle">doc title goes here</h1>
    <ul tdi:scope="menu">
        <li tdi="item"><a tdi="link">some menu item</a></li><li tdi=":-item">
        </li>
    </ul>
    <p tdi="intro" class="edit-intro">Intro goes here.</p>
    <div class="list" tdi="list">
        ...
    </div>
</body>
</html>
""")


# BEGIN INCLUDE
class Menu(object):
    def __init__(self, menu, page):
        self._menu = menu
        self._page = page

    def render_item(self, node):
        node.repeat(self.repeat_item, self._menu)

    def repeat_item(self, node, (href, menuitem)):
        node.link.content = menuitem
        if (node.ctx[0] + 1 == self._page):
            node.link.hiddenelement = True
        else:
            node.link['href'] = href


class Model(object):
    def __init__(self, menu, page):
        self.scope_menu = Menu(menu, page)
#END INCLUDE

menu = [
    (u'/some/', u'Some Menu Item'),
    (u'/other/', u'Editing Content & Attributes'),
    (u'/third.html', u'Another Menu Item'),
]
model = Model(menu=menu, page=2)
template.render(model)
