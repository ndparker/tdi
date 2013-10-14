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
    <ul class="menu">
        <li><a href="menu1" tdi="menu1">some menu item</a></li>
        <li><a href="menu2" tdi="menu2">Editing Content &amp; Attributes</a></li>
        <li><a href="menu3" tdi="menu3">Other menu item</a></li>
    </ul>
    <p tdi="intro" class="edit-intro">Intro goes here.</p>
    <div class="list" tdi="list">
        ...
    </div>
</body>
</html>
""")

class Model(object):
    def __init__(self, possibilities, page):
        self._possibilities = possibilities
        self._page = page

    def render_doctitle(self, node):
        node.content = u"Editing Content & Attributes"

    def render_menu1(self, node):
        if self._page == 1:
            node.hiddenelement = True

    def render_menu2(self, node):
        if self._page == 2:
            node.hiddenelement = True

    def render_menu3(self, node):
        if self._page == 3:
            node.hiddenelement = True

    def render_intro(self, node):
        if not self._possibilities:
            del node['class']
            node.content = u"There are no possibilities listed right now."
        else:
            node.content = u"Modifying content and markup attributes is easy."

    def render_list(self, node):
        if not self._possibilities:
            node.remove()
            return
        # fill in possibilities here...

model = Model(possibilities=(), page=2)
template.render(model)
