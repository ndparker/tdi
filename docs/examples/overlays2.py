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
    <ul tdi:overlay="menu" tdi="mymenu"></ul>
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
    <ul tdi:overlay="menu" tdi="menucontainer">
        <li tdi="menu"><a tdi="link">some menu item</a></li><li tdi=":-menu">
        </li>
    </ul>
</body>
</html>
""")

class Model(object):
    def render_menucontainer(self, node):
        print "menucontainer"

    def render_mymenu(self, node):
        print "mymenu"


model = Model()
template = content.overlay(menu_widget)
template.render_string(model)
