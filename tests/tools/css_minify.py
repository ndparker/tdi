#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import css

x = css.minify(u"""
body {
    background-color: #fff;
}
""")
print repr(x)

x = css.minify("""
.eacute:after {
    content: "\xe9";
}
""")
print repr(x)

try:
    x = css.minify("""
    .eacute:after {
        content: "\xe9";
    }
    """, encoding='utf-8')
except UnicodeError:
    print "UnicodeError - OK"

x = css.minify("""
.eacute:after {
    content: "\xc3\xa9";
}
""", encoding='utf-8')
print repr(x)
