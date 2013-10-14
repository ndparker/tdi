#!/usr/bin/env python
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
from tdi.tools import javascript

script = u'''
var a = __var__;
var b = '__str__';
'''.strip()
print javascript.replace(script, dict(
    var=javascript.SimpleJSON([1, 2, 3, 4]),
    str=u'my "string"'
))
