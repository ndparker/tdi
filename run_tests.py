#!/usr/bin/env python
# -*- coding: ascii -*-
#
# Copyright 2006 - 2013
# Andr\xe9 Malo or his licensors, as applicable
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
===========
 Run tests
===========

Run tests.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import os as _os
import re as _re
import sys as _sys

from _setup import shell
from _setup import term


def _make_sort_attr():
    tag_sub = _re.compile(r'<([^/>\s]+)\s([^>]+)>').sub
    attr_find = _re.compile(r'[^\s"]*(?:"[^"]*"[^\s"]*)*').findall
    def sort_attr(value):
        """ Sort attributes to avoid dict-ordering related test failures """
        def subber(m):
            attr = filter(None, attr_find(m.group(2)))
            attr.sort()
            return '<%s %s>' % (m.group(1), ' '.join(attr))
        if value is None:
            return None
        return tag_sub(subber, value)
    return sort_attr
sort_attr = _make_sort_attr()


def run_tests(basedir, libdir):
    """ Run output based tests """

    def run_test(script, output):
        """ Run it """
        erred = 0
        try:
            fp = open(output, 'r')
        except IOError:
            output = None
        else:
            try:
                output = fp.read()
            finally:
                fp.close()
        env = dict(_os.environ)
        if libdir is not None:
            libdir_ = shell.native(libdir)
            if env.has_key('PYTHONPATH'):
                ppath = _os.pathsep.join((libdir_, env['PYTHONPATH']))
            else:
                ppath = libdir_
            env['PYTHONPATH'] = libdir_
        out = ""
        overrides = '10'
        if 'java' in _sys.platform.lower() or \
                getattr(_sys, 'pypy_version_info', None) is not None:
            overrides = '1'
        for no_c_override in overrides:
            env['TDI_NO_C_OVERRIDE'] = no_c_override
            try:
                genout = shell.spawn(
                    _sys.executable, script, stdout=True, env=env
                )
            except shell.SignalError, e:
                out += "%%(RED)s%s%%(NORMAL)s " % (e.signalstr,)
                erred = 1
            except shell.ExitError, e:
                out += "%%(RED)s  %02d%%(NORMAL)s " % e.code
                erred = 1
            else:
                if genout != output:
                    genout = sort_attr(genout)
                    output = sort_attr(output)
                if genout == output:
                    out += "%(GREEN)sOK%(NORMAL)s   "
                else:
                    out += "%(RED)sfail%(NORMAL)s "
                    erred = 1
        out += "- %(script)s\n"
        term.write(out, script=_os.path.basename(script))
        return erred

    # end
    # begin main test code

    erred = 0
    basedir = shell.native(basedir)
    strip = len(basedir) - len(_os.path.basename(basedir))
    for dirname, dirs, files in shell.walk(basedir):
        dirs[:] = [item for item in dirs if item not in ('.svn', 'out')]
        dirs.sort()
        files = [item for item in files if item.endswith('.py')]
        if not files:
            continue
        if not _os.path.isdir(_os.path.join(basedir, dirname, 'out')):
            continue
        term.yellow("---> %s" % (dirname[strip:],))
        files.sort()
        for filename in files:
            if run_test(
                _os.path.join(dirname, filename),
                _os.path.join(dirname, 'out', filename[:-3] + '.out'),
            ): erred = 1
        term.yellow("<--- %s" % (dirname[strip:],))
    return erred


def main():
    """ Main """
    basedir, libdir = None, None
    accept_opts = True
    args = []
    for arg in _sys.argv[1:]:
        if accept_opts:
            if arg == '--':
                accept_opts = False
                continue
            elif arg == '-q':
                term.write = term.green = term.red = term.yellow = \
                    term.announce = \
                    lambda fmt, **kwargs: None
                continue
            elif arg == '-p':
                info = {}
                for key in term.terminfo():
                    info[key] = ''
                info['ERASE'] = '\n'
                term.terminfo.info = info
                continue
            elif arg.startswith('-'):
                _sys.stderr.write("Unrecognized option %r\n" % (arg,))
                return 2
        args.append(arg)
    if len(args) > 2:
        _sys.stderr.write("Too many arguments\n")
        return 2
    elif len(args) < 1:
        _sys.stderr.write("Missing arguments\n")
        return 2
    basedir = args[0]
    if len(args) > 1:
        libdir = args[1]
    return run_tests(basedir, libdir)


if __name__ == '__main__':
    _sys.exit(main())
