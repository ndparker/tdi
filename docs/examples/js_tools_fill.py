#!/usr/bin/env python
# -*- coding: utf-8 -*-
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import javascript
try:
    javascript.SimpleJSON([]).as_json()
except ImportError:
    class json(object):
        def __init__(self, val):
            pass
        def as_json(self, **kw):
            return u'[1,2,3,4]'
    javascript.SimpleJSON = json

# BEGIN INCLUDE
from tdi import html
from tdi.tools import javascript

tpl = html.from_string('''
<button tdi="button" onclick="alert('__alert__')">
    Click me!
</button>
<script tdi="script">
var a = __var__;
var b = '__str__';
</script>
'''.lstrip())


class Model(object):
    def render_button(self, node):
        javascript.fill_attr(node, 'onclick', dict(
            alert=u'"Hey André! ---]]>"'
        ))

    def render_script(self, node):
        javascript.fill(node, dict(
            var=javascript.SimpleJSON([1, 2, 3, 4]),
            str=u'"Hey André! ---]]>"',
        ))

tpl.render(Model())
