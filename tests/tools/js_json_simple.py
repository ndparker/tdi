#!/usr/bin/env python
import sys as _sys
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import javascript

try:
    unicode(javascript.SimpleJSON(u''))
except ImportError: # fake output. easy skipping is not possible...
    print """SimpleJSON({1: u'Andr\\xe9 \\u2028\\u2029</---]]>'}, False)
'{"1":"Andr\\xc3\\xa9 \\\\u2028\\\\u2029</---]]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029</---]]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029</---]]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029<\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029</---]]>"}'
SimpleJSON({1: u'Andr\\xe9 \\u2028\\u2029</---]]>'}, True)
'{"1":"Andr\\xc3\\xa9 \\\\u2028\\\\u2029<\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029<\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029<\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029<\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 \\\\u2028\\\\u2029</---]]>"}'
SimpleJSON({1: 'Andr\\xe9 </---]]>'}, False)
'{"1":"Andr\\xc3\\xa9 </---]]>"}'
u'{"1":"Andr\\xe9 </---]]>"}'
u'{"1":"Andr\\xe9 </---]]>"}'
u'{"1":"Andr\\xe9 <\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 </---]]>"}'
SimpleJSON({1: 'Andr\\xe9 </---]]>'}, True)
'{"1":"Andr\\xc3\\xa9 <\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 <\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 <\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 <\\\\/-\\\\-\\\\-]\\\\]>"}'
u'{"1":"Andr\\xe9 </---]]>"}'"""
    _sys.exit(0)


x = javascript.SimpleJSON({1: u'Andr\xe9 \u2028\u2029</---]]>'})
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))

x = javascript.SimpleJSON({1: u'Andr\xe9 \u2028\u2029</---]]>'}, inlined=True)
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))

x = javascript.SimpleJSON({1: 'Andr\xe9 </---]]>'})
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))

x = javascript.SimpleJSON({1: 'Andr\xe9 </---]]>'}, inlined=True)
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))
