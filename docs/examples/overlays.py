#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
content = html.from_string("""
<html>
<body>
    <h1 tdi="doctitle">doc title goes here</h1>
    <ul tdi:overlay="menu"></ul>
    <p tdi="intro" class="edit-intro">Intro goes here.</p>
    <div class="list" tdi="list">
        ...
    </div>
</body>
</html>
""")
menu_widget = html.from_string("""
<html>
<body>
    <ul tdi:overlay="menu">
        <li tdi="menu"><a tdi="link">some menu item</a></li><li tdi=":-menu">
        </li>
    </ul>
</body>
</html>
""")

class Model(object):
    def __init__(self, menu, page):
        self._menu = menu
        self._page = page

    def render_menu(self, node):
        node.repeat(self.repeat_menu, self._menu)

    def repeat_menu(self, node, (href, menuitem)):
        node.link.content = menuitem
        if (node.ctx[0] + 1 == self._page):
            node.link.hiddenelement = True
        else:
            node.link['href'] = href

menu = [
    (u'/some/', u'Some Menu Item'),
    (u'/other/', u'Editing Content & Attributes'),
    (u'/third.html', u'Another Menu Item'),
]
model = Model(menu=menu, page=2)

template = content.overlay(menu_widget)
template.render(model)
