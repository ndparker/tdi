#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi.tools import html as html_tools
from tdi import html

tpl = html.replace(eventfilters=[
    html_tools.MinifyFilter
]).from_string("""
<html>
<head>
    <title>Hello World!</title>
    <style>/*<![CDATA[*/
        Some    style.
    /*]]>*/</style>
</head>
<body>
    <script>//<![CDATA[
        Some    script.
    //]]></script>
    <h1>Hello World!</h1>
</body>
""".lstrip())

tpl.render()
