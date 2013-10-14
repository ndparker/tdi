#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import html

result = html.decode('Andr&eacute; Malo, \x80', 'cp1252')
print result.encode('unicode_escape')
print result.encode('utf-8')
