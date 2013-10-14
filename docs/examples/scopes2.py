#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
template = html.from_string("""
<html>
<body>
    <ul tdi:scope="navigation">
        <li tdi="breadcrumb"><a tdi="*link"></a></li><li tdi=":-breadcrumb">
        </li>
    </ul>
    ...
    <ul tdi:scope="navigation">
        <li tdi="menu"><a tdi="*link">some menu item</a></li><li tdi=":-menu">
        </li>
    </ul>
</body>
</html>
""".lstrip())


class Navigation(object):
    def __init__(self, breadcrumb, menu, page):
        self._breadcrumb = breadcrumb
        self._menu = menu
        self._page = page

    def render_breadcrumb(self, node):
        node.repeat(self.repeat_nav, self._breadcrumb,
            len(self._breadcrumb) - 1
        )

    def render_menu(self, node):
        node.repeat(self.repeat_nav, self._menu,
            self._page - 1
        )

    def repeat_nav(self, node, (href, menuitem), active):
        node.link.content = menuitem
        if (node.ctx[0] == active):
            node.link.hiddenelement = True
        else:
            node.link['href'] = href


class Model(object):
    def __init__(self, breadcrumb, menu, page):
        self.scope_navigation = Navigation(breadcrumb, menu, page)


menu = [
    (u'/some/', u'Some Menu Item'),
    (u'/other/', u'Editing Content & Attributes'),
    (u'/third.html', u'Another Menu Item'),
]
breadcrumb = [
    (u'/', u'Hompage'),
    (u'/other/', u'Editing Content & Attributes'),
]
model = Model(breadcrumb=breadcrumb, menu=menu, page=2)
template.render(model)
