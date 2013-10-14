#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import sys
import tempfile
import time

from tdi import html

html = html.replace(autoupdate=True)

tfile = tempfile.NamedTemporaryFile()
try:
    tfile.write("""<html><body tdi="body">Yey</body></html>""")
    tfile.flush()

    # 2) Load the template from_file
    template = html.from_file(tfile.name)
    print template.tree

    # (... wait for low-timer-resolution systems ...)
    time.sleep(3)

    # 3) Update the file
    tfile.seek(0)
    tfile.truncate()
    tfile.write("""<html><body tdi="nobody">Yup!</body></html>""")
    tfile.flush()

    # 4) Voila
    print template.tree

finally:
    tfile.close()
