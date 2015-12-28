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

=======================
 Tests for tdi.filters
=======================

Tests for tdi.filters
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals, assert_true
from .. import _util as _test

from tdi import filters as _filters


def test_basestream_init():
    """ BaseStreamFilter initializes properly """
    result = _filters.BaseStreamFilter('FOO')

    assert_true(isinstance(result, _filters.BaseStreamFilter))
    tresult = type(result)

    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.filters.BaseStreamFilter')


def test_basestream_delegate():
    """ BaseStreamFilter delegates properly """
    inst = _filters.BaseStreamFilter(_test.Bunch(blahr=42))

    result = inst.blahr

    assert_equals(result, 42)


def test_streamfilename_init():
    """ StreamFilename initializes properly """
    result = _filters.StreamFilename('FOO', 'BAR')

    assert_true(isinstance(result, _filters.StreamFilename))
    assert_true(isinstance(result, _filters.BaseStreamFilter))

    tresult = type(result)
    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.filters.StreamFilename')
    assert_equals(result.filename, 'BAR')


@_test.multi_impl(globals(), _filters, name='impl')
def test_baseevent_init(impl):
    """ BaseEventFilter initializes properly """
    result = _filters.BaseEventFilter('FOO')

    assert_true(isinstance(result, _filters.BaseEventFilter))
    tresult = type(result)

    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.c._tdi_impl.BaseEventFilter' if impl == 'c' else
                  'tdi.filters.BaseEventFilter')
    assert_equals(result.builder, 'FOO')


@_test.multi_impl(globals(), _filters)
def test_baseevent_delegate():
    """ BaseEventFilter delegates properly """
    inst = _filters.BaseEventFilter(_test.Bunch(blahr=43))

    result = inst.blahr

    assert_equals(result, 43)


def test_filterfilename_init():
    """ FilterFilename initializes properly """
    result = _filters.FilterFilename('FOO', 'BAR')

    assert_true(isinstance(result, _filters.FilterFilename))
    assert_true(isinstance(result, _filters.BaseEventFilter))

    tresult = type(result)
    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.filters.FilterFilename')
    assert_equals(result.filename, 'BAR')
