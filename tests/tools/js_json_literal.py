#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import javascript

x = javascript.LiteralJSON(u'Andr\xe9 \u2028\u2029</---]]>')
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))

x = javascript.LiteralJSON(u'Andr\xe9 \u2028\u2029</---]]>', inlined=True)
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))

x = javascript.LiteralJSON('Andr\xc3\xa9 \xe2\x80\xa8\xe2\x80\xa9</---]]>',
    encoding='utf-8'
)
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))

x = javascript.LiteralJSON('Andr\xc3\xa9 \xe2\x80\xa8\xe2\x80\xa9</---]]>',
    encoding='utf-8', inlined=True
)
print repr(x)
print repr(str(x))
print repr(unicode(x))
print repr(x.as_json())
print repr(x.as_json(inlined=True))
print repr(x.as_json(inlined=False))

x = javascript.LiteralJSON('Andr\xe9 \xe2\x80\xa8\xe2\x80\xa9</---]]>',
    encoding='utf-8'
)
print repr(x)
try:
    print repr(str(x))
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(unicode(x))
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(x.as_json())
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(x.as_json(inlined=True))
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(x.as_json(inlined=False))
except UnicodeError:
    print "UnicodeError - OK"

x = javascript.LiteralJSON('Andr\xe9 \xe2\x80\xa8\xe2\x80\xa9</---]]>',
    encoding='utf-8', inlined=True
)
print repr(x)
try:
    print repr(str(x))
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(unicode(x))
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(x.as_json())
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(x.as_json(inlined=True))
except UnicodeError:
    print "UnicodeError - OK"
try:
    print repr(x.as_json(inlined=False))
except UnicodeError:
    print "UnicodeError - OK"
