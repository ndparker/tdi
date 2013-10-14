#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

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
    <!-- foo -->
    <script>
        Some script.
    </script>
    <h1>Hello World!</h1>
    <!-- bar -->
</body>
""".lstrip(), cdata_containers=True)
