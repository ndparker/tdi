#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import javascript

x = javascript.escape_inlined(u'\xe9-------]]></script>')
print repr(x)

x = javascript.escape_inlined('\xe9-------]]></script>')
print repr(x)

try:
    javascript.escape_inlined('\xe9-------]]></script>', encoding='utf-8')
except UnicodeError:
    print "UnicodeError - OK"

x = javascript.escape_inlined('\xc3\xa9-------]]></script>', encoding='utf-8')
print repr(x)


