#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import html

print html.multiline(u"""
H\xe9llo World!

In December 2012 the world will go down.
\tBye world<!>
""".lstrip(), xhtml=False)
