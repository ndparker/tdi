#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import javascript

print javascript.minify(u"""
if (n.tagName.toLowerCase() == 'label') {
    n = n.parentNode;
    if (t && n == t) continue;
    t = n;
}
""".lstrip())
