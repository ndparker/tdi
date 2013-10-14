#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import os
os.chdir(os.path.dirname(os.path.abspath(os.path.normpath(__file__))))

# BEGIN INCLUDE
from tdi import html
from tdi import factory

template = html.from_string("""
<html>
<body tdi="body">
    some template
</body>
</html>
""")
print template.tree

template = html.from_file('loading.html')
print template.tree

stream = open('loading.html')
try:
    template = html.from_stream(stream)
finally:
    stream.close()
print template.tree

template = html.from_opener(factory.file_opener, 'loading.html')
print template.tree
