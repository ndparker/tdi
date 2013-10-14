#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
from tdi.tools import html as html_tools

# 1. Comment filter
def keep_foo(comment):
    """ Comment filter """
    if comment == "<!-- foo -->":
        return comment

# 2. New filter factory
def html_minifyfilter(builder):
    """ HTML minifier factory """
    return html_tools.MinifyFilter(builder, comment_filter=keep_foo)

# 3. Template Factory
html = html.replace(eventfilters=[
    # ...
    html_minifyfilter, # instead of html_tools.MinifyFilter
    # ...
])

# 4. Do your thing.
tpl = html.from_string("""
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
""".lstrip())
tpl.render()
