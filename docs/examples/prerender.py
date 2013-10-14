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
    <ul>
        <li tdi="menu"><a tdi="link">some menu item</a></li><li tdi=":-menu">
        </li>
    </ul>
    <p tdi="intro" class="edit-intro">Intro goes here.</p>
    <div class="list" tdi="list">
        ...
    </div>
</body>
</html>
""")

class PreModel(object):
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

class Model(object):
    def render_doctitle(self, node):
        node.content = u"Some title"

menu = [
    (u'/some/', u'Some Menu Item'),
    (u'/other/', u'Editing Content & Attributes'),
    (u'/third.html', u'Another Menu Item'),
]
premodel = PreModel(menu=menu, page=2)
model = Model()
template.render(model, prerender=premodel)
