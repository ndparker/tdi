#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

import time
import sys

def wait():
    for _ in xrange(3):
        time.sleep(1)
        sys.stdout.write('.')
        sys.stdout.flush()
    print "\n"

# BEGIN INCLUDE
import tempfile
from tdi import html

# 1) Tell the factory that we want automatic template updates
html = html.replace(autoupdate=True)

tfile = tempfile.NamedTemporaryFile()
try:
    tfile.write("""<html><body tdi="body">Yey</body></html>""")
    tfile.flush()

    # 2) Load the template from_file
    template = html.from_file(tfile.name)
    print template.tree

    # (... wait for low-timer-resolution systems ...)
    wait()

    # 3) Update the file
    tfile.seek(0)
    tfile.truncate()
    tfile.write("""<html><body tdi="nobody">Yup!</body></html>""")
    tfile.flush()

    # 4) Voila
    print template.tree

finally:
    tfile.close()
