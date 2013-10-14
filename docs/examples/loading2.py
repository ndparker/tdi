#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
import tempfile
from tdi import html

file_1 = tempfile.NamedTemporaryFile()
try:
    file_2 = tempfile.NamedTemporaryFile()
    try:
        file_1.write("""<html lang="en"><body tdi:overlay="huh">yay.</body></html>""")
        file_1.flush()

        file_2.write("""<html><body tdi:overlay="huh">file 2!</body></html>""")
        file_2.flush()

        template = html.from_files([file_1.name, file_2.name])
    finally:
        file_2.close()
finally:
    file_1.close()

template.render()
