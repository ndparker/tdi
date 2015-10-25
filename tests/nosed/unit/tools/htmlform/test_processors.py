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

==========================================
 Tests for tdi.tools.htmlform._processors
==========================================

Tests for tdi.tools.htmlform._processors
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals
import mock as _mock

from tdi.tools.htmlform import _processors


def test_tabindexer_init():
    """ TabIndexer inits properly """
    inst = _processors.TabIndexer()

    assert_equals(sorted(inst.__dict__.keys()), ['next_index'])
    assert_equals(inst.next_index(), 1)
    assert_equals(inst.next_index(), 2)


def test_tabindexer_call():
    """ TabIndexer.__call__() sets tabindex """
    inst = _processors.TabIndexer()

    node1 = _mock.MagicMock()
    node2 = _mock.MagicMock()
    node3 = _mock.MagicMock()

    inst('text', node1, None)
    inst('form', node2, None)
    inst('fooo', node3, None)

    assert_equals(map(tuple, node1.mock_calls), [
        ('__setitem__', ('tabindex', 1), {}),
    ])
    assert_equals(map(tuple, node2.mock_calls), [])
    assert_equals(map(tuple, node3.mock_calls), [
        ('__setitem__', ('tabindex', 2), {}),
    ])
