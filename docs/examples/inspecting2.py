#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import html
template = html.from_string("""
<html>
<body>
    <h1 tdi="doctitle">doc title goes here</h1>
    <p tdi="intro">Intro goes <span tdi="where">here</span>.</p>
</body>
</html>
""")

# BEGIN INCLUDE
print template.tree.to_string(verbose=True)
