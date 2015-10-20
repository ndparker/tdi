# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2014 - 2015
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

==========================
 Tests for tdi.interfaces
==========================

Tests for tdi.interfaces.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"


from nose.tools import assert_true, assert_false
from .._util import Bunch

from tdi import interfaces as _interfaces


# test interfaces
class IF1(object):  # pylint: disable = missing-docstring
    pass


class IF2(object):  # pylint: disable = missing-docstring
    pass


class IF3(object):  # pylint: disable = missing-docstring
    pass


class IF4(IF2):  # pylint: disable = missing-docstring
    pass


class IF5:  # pylint: disable = missing-docstring, old-style-class, no-init
    pass


def test_implements_no_interface():
    """ interfaces.implements handles non-implementing objects """
    assert_false(_interfaces.implements(Bunch(), 'lalal'))


def test_implements_no_interface_2():
    """ interfaces.implements handles empty interface list  """
    assert_false(_interfaces.implements(Bunch()))


def test_implements_all_ok():
    """ interfaces.implements finds all interfaces """
    assert_true(_interfaces.implements(Bunch(__implements__=[
        IF1, IF2
    ]), IF1, IF2))


def test_implements_sub_ok():
    """ interfaces.implements finds subclassed interfaces """
    assert_true(_interfaces.implements(Bunch(__implements__=[
        IF1, IF4
    ]), IF1, IF2))


def test_implements_sub_nok():
    """ interfaces.implements rejects super interfaces """
    assert_false(_interfaces.implements(Bunch(__implements__=[
        IF1, IF2
    ]), IF1, IF4))


def test_implements_missing_fail():
    """ interfaces.implements rejects missing interfaces """
    assert_false(_interfaces.implements(Bunch(__implements__=[
        IF1, IF4
    ]), IF1, IF2, IF3))


def test_implements_extra_ok():
    """ interfaces.implements accepts extra interfaces """
    assert_true(_interfaces.implements(Bunch(__implements__=[
        IF1, IF4, IF3
    ]), IF1, IF2))


def test_implements_accept_oldstyle():
    """ interfaces.implements accepts old-style interface classes """
    assert_true(_interfaces.implements(Bunch(__implements__=[
        IF1, IF5
    ]), IF5))


def test_implements_reject_nonclasses():
    """ interfaces.implements rejects non-class interfaces """
    assert_false(_interfaces.implements(Bunch(__implements__=[
        1, IF1
    ]), 1))
