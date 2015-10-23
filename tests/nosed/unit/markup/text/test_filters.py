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

===================================
 Tests for tdi.markup.text.filters
===================================

Tests for tdi._util
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals
import mock as _mock

from tdi.markup.text import filters as _filters


def test_handle_pi_apply():
    """ text/EncodingDetectFilter() applies encoding """
    builder = _mock.MagicMock()
    inst = _filters.EncodingDetectFilter(builder)

    inst.handle_pi('[?encodinG rot13 ?]')

    assert_equals(map(tuple, builder.mock_calls), [
        ('handle_encoding', ('rot13',), {}),
        ('handle_pi', ('[?encodinG rot13 ?]',), {}),
    ])


def test_handle_pi_opaque():
    """ text/EncodingDetectFilter() ignores non-encoding """
    builder = _mock.MagicMock()
    inst = _filters.EncodingDetectFilter(builder)

    inst.handle_pi('some data')

    assert_equals(map(tuple, builder.mock_calls), [
        ('handle_pi', ('some data',), {}),
    ])
