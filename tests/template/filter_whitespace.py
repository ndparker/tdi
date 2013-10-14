#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.tools import html as _html_tools
from tdi import html

html_compressed = html.replace(eventfilters=[_html_tools.MinifyFilter])

template = html_compressed.from_string("""
<html>
<head>
    <title>Boo! </title>
    <script>
        Some script
    </script>
    <style><!--
        Some style
    --></style>
</head>
<body>
    <p>Hello <b>YOU!</b> reader!

    Now...      <br />
    <form>
        <textarea   >Some
text
in     here.
        </textarea >
    </form>

    <!-- Comment! -->
    <pre>
        More text

            in


                here.
    </pre>
</body>
</html  >
abc

""")

template.render()
print
