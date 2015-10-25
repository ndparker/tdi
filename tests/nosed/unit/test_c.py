# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2015
 Andr\xe9 Malo or his licensors, as applicable

:License:

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

=====================
 Tests for tdi._util
=====================

Tests for tdi._util
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals

from tdi import c as _c

from .. import _util as _test

# pylint: disable = invalid-name


def test_globals():
    """ c globals contain documented values """
    result = dict((key, value) for key, value in vars(_c).iteritems()
                  if not key.startswith('_') and key != 'load')

    assert_equals(result, {
        'DEFAULT_ENV_OVERRIDE': 'TDI_NO_C_OVERRIDE',
        'DEFAULT_TPL': 'tdi.c._tdi_%s',
    })


@_test.patch(_c, '__import__', name='imp')
@_test.patch(_c, '_os', name='os')
@_test.patch(_c, 'globals', name='glob')
def test_load(imp, os, glob):
    """ c.load() imports and returns a module """
    imp.side_effect = ['lalala']
    os.environ.get.side_effect = [None]
    glob.side_effect = [dict(a=1, b=2)]

    result = _c.load('foo')

    assert_equals(result, 'lalala')
    assert_equals(map(tuple, imp.mock_calls), [
        ('', ('tdi.c._tdi_foo', {'a': 1, 'b': 2},
              {'modname': 'foo', 'tpl': 'tdi.c._tdi_%s',
               'env_override': 'TDI_NO_C_OVERRIDE'}, ['*']), {}),
    ])
    assert_equals(map(tuple, os.mock_calls), [
        ('environ.get', ('TDI_NO_C_OVERRIDE',), {}),
    ])
    assert_equals(map(tuple, glob.mock_calls), [('', (), {})])


@_test.patch(_c, '__import__', name='imp')
@_test.patch(_c, '_os', name='os')
@_test.patch(_c, 'globals', name='glob')
def test_load_override(imp, os, glob):
    """ c.load() accepts different override """
    imp.side_effect = ['lalala']
    os.environ.get.side_effect = [None]
    glob.side_effect = [dict(a=1, b=2)]

    result = _c.load('foo', env_override='YO')

    assert_equals(result, 'lalala')
    assert_equals(map(tuple, imp.mock_calls), [
        ('', ('tdi.c._tdi_foo', {'a': 1, 'b': 2},
              {'modname': 'foo', 'tpl': 'tdi.c._tdi_%s',
               'env_override': 'YO'}, ['*']), {}),
    ])
    assert_equals(map(tuple, os.mock_calls), [
        ('environ.get', ('YO',), {}),
    ])
    assert_equals(map(tuple, glob.mock_calls), [('', (), {})])


@_test.patch(_c, '__import__', name='imp')
@_test.patch(_c, '_os', name='os')
@_test.patch(_c, 'globals', name='glob')
def test_load_tpl(imp, os, glob):
    """ c.load() accepts different template """
    imp.side_effect = ['lalala']
    os.environ.get.side_effect = [None]
    glob.side_effect = [dict(a=1, b=2)]

    result = _c.load('foo', tpl='_xx_%s_yy_')

    assert_equals(result, 'lalala')
    assert_equals(map(tuple, imp.mock_calls), [
        ('', ('_xx_foo_yy_', {'a': 1, 'b': 2},
              {'modname': 'foo', 'tpl': '_xx_%s_yy_',
               'env_override': 'TDI_NO_C_OVERRIDE'}, ['*']), {}),
    ])
    assert_equals(map(tuple, os.mock_calls), [
        ('environ.get', ('TDI_NO_C_OVERRIDE',), {}),
    ])
    assert_equals(map(tuple, glob.mock_calls), [('', (), {})])


@_test.patch(_c, '__import__', name='imp')
@_test.patch(_c, '_os', name='os')
def test_load_none(imp, os):
    """ c.load() returns None if overridden """
    imp.side_effect = []
    os.environ.get.side_effect = ["1"]

    result = _c.load('foo')

    assert_equals(result, None)
    assert_equals(map(tuple, imp.mock_calls), [])
    assert_equals(map(tuple, os.mock_calls), [
        ('environ.get', ('TDI_NO_C_OVERRIDE',), {}),
    ])


@_test.patch(_c, '__import__', name='imp')
@_test.patch(_c, '_os', name='os')
@_test.patch(_c, 'globals', name='glob')
def test_load_error(imp, os, glob):
    """ c.load() returns None on import error """
    imp.side_effect = [ImportError]
    os.environ.get.side_effect = [None]
    glob.side_effect = [dict(a=1, b=2)]

    result = _c.load('foo')

    assert_equals(result, None)
    assert_equals(map(tuple, imp.mock_calls), [
        ('', ('tdi.c._tdi_foo', {'a': 1, 'b': 2},
              {'modname': 'foo', 'tpl': 'tdi.c._tdi_%s',
               'env_override': 'TDI_NO_C_OVERRIDE'}, ['*']), {}),
    ])
    assert_equals(map(tuple, os.mock_calls), [
        ('environ.get', ('TDI_NO_C_OVERRIDE',), {}),
    ])
    assert_equals(map(tuple, glob.mock_calls), [('', (), {})])
