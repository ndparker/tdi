#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import html

print html.minify(u"""
<html>
<head>
    <!-- Here comes the title -->
    <title>Hello World!</title>
    <style>
        Some style.
    </style>
</head>
<body>
    <script>
        Some script.
    </script>
    <h1>Hello World!</h1>
</body>
""".lstrip())
