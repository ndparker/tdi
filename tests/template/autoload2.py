#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import sys
import tempfile
import time

from tdi import html

html = html.replace(autoupdate=True)

tfile1 = tempfile.NamedTemporaryFile()
try:
    tfile1.write(
        """<html><body tdi="body" tdi:overlay=">foo">Yey</body></html>"""
    )
    tfile1.flush()

    tfile2 = tempfile.NamedTemporaryFile()
    try:
        tfile2.write("""<tdi tdi:overlay="foo">blub</tdi>""")
        tfile2.flush()

        # 2) Load the template from_file
        template = (
            html.from_file(tfile1.name)
            .overlay(html.from_file(tfile2.name))
        )
        print template.tree

        # (... wait for low-timer-resolution systems ...)
        time.sleep(3)

        # 3) Update the file
        tfile1.seek(0)
        tfile1.truncate()
        tfile1.write(
            """<xhtml><body tdi="nobody" tdi:overlay="foo">"""
            """Yup!</body></xhtml>"""
        )
        tfile1.flush()

        # 4) Voila
        print template.tree
    finally:
        tfile2.close()
finally:
    tfile1.close()
