#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import javascript

x = javascript.escape_string(u'\xe9--"\'\\-----]]></script>')
print type(x).__name__, x

x = javascript.escape_string(u'\xe9---"\'\\----]]></script>', inlined=False)
print type(x).__name__, x

x = javascript.escape_string('\xe9--"\'\\-----]]></script>')
print type(x).__name__, x

x = javascript.escape_string('\xe9---"\'\\----]]></script>', inlined=False)
print type(x).__name__, x

try:
    x = javascript.escape_string('\xe9--"\'\\-----]]></script>',
        encoding='utf-8'
    )
except UnicodeError:
    print "UnicodeError - OK"

try:
    x = javascript.escape_string('\xe9--"\'\\-----]]></script>',
        inlined=False, encoding='utf-8'
    )
except UnicodeError:
    print "UnicodeError - OK"

x = javascript.escape_string('\xc3\xa9---"\'\\----]]></script>',
    encoding='utf-8'
)
print type(x).__name__, x

x = javascript.escape_string('\xc3\xa9---"\'\\----]]></script>',
    inlined=False, encoding='utf-8'
)
print type(x).__name__, x

# Bigunicode test: &afr; - MATHEMATICAL FRAKTUR SMALL A
# 1st: the real character must be replaced by surrogates.
# 2nd: The unreal one must stay.
a, s = u'a', u'\\'
for u in ('5\xd8\x1e\xdd'.decode("utf-16-le"), u'\\U0001d51e'):
    for c in xrange(5):
        x = javascript.escape_string(s * c + u + u'--"\'\\-----]]></script>')
        print type(x).__name__, x

        x = javascript.escape_string(s * c + u + u'--"\'\\-----]]></script>',
            inlined=False
        )
        print type(x).__name__, x

        x = javascript.escape_string(a + s * c + u + u'-"\'\\---]]></script>')
        print type(x).__name__, x

        x = javascript.escape_string(a + s * c + u + u'-"\'\\---]]></script>',
            inlined = False
        )
        print type(x).__name__, x
