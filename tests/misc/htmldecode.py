#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import _htmldecode
def d(*a, **k):
    try:
        return repr(_htmldecode.decode(*a, **k))
    except UnicodeError:
        return "unicodeerror"
    except ValueError, e:
        return str(e)

for _ in xrange(10):
    print d('xx&#66;&&aleph;&lalalala;', errors='strict')
    print d('xx&#66;&&aleph;&lalalala;')
    print d('xx&#66;&lt;&&aleph;&lalalala;', errors='ignore')
    print d('xx&#66;&lt;&&aleph;&lalalala;', errors='replace')
    print d('&x;&x;&x;', entities={u'x': u'AAAAAAAAAA'})
    print d('&#;')
    print d('&#x;')
    print d('&#x41;')
    print d('&#xffFFffFF;')
    print d('&#1234567890;')
    print d('&#xffFFffFF;', errors='ignore')
    print d('&#1234567890;', errors='ignore')
    print d('&#xffFFffFF;', errors='replace')
    print d('&#1234567890;', errors='replace')
    print d('\xe9', encoding='utf-8')
    print d('\xe9', encoding='utf-8', errors='ignore')
    print d('\xe9', encoding='utf-8', errors='replace')
    print d('\xc3\xa9', encoding='utf-8')

