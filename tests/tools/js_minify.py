#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import javascript

x = javascript.minify(u"""
var x=1;
var y = 2; \xe9
alert( x + y );
""")
print repr(x)

x = javascript.minify("""
var x=1;
var y = 2; \xe9
alert( x + y );
""")
print repr(x)

try:
    x = javascript.minify("""
    var x=1;
    var y = 2; \xe9
    alert( x + y );
    """, encoding='utf-8')
except UnicodeError:
    print "UnicodeError - OK"

x = javascript.minify("""
var x=1;
var y = 2; \xc3\xa9
alert( x + y );
""", encoding='utf-8')
print repr(x)
