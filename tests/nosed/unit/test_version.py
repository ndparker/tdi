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

========================
 Tests for tdi._version
========================

Tests for tdi._version
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals, assert_true, assert_false

from tdi import _version


def test_basic_tuple():
    """ Version yields at least 3-tuples """
    ver = _version.Version("1.2.3", False, 4)
    assert_equals(ver, (1, 2, 3))

    ver = _version.Version("1.2.3", True, 4)
    assert_equals(ver, (1, 2, 3))

    ver = _version.Version("1.2", True, 4)
    assert_equals(ver, (1, 2, 0))


def test_extended_tuple():
    """ Version accepts more than 3 parts, also non-int """
    ver = _version.Version("1.2.3.4.foo", True, 5)
    assert_equals(ver, (1, 2, 3, 4, 'foo'))


def test_attributes():
    """ Version fills attributes properly """
    ver = _version.Version("1.2.3.4.foo", True, 5)
    assert_equals(ver.major, 1)
    assert_equals(ver.minor, 2)
    assert_equals(ver.patch, 3)
    assert_equals(ver.revision, 5)
    assert_true(ver.is_dev)

    ver = _version.Version("2.3.4.5.foo", False, 6)
    assert_equals(ver.major, 2)
    assert_equals(ver.minor, 3)
    assert_equals(ver.patch, 4)
    assert_equals(ver.revision, 6)
    assert_false(ver.is_dev)


def test_string():
    """ Version produces reasonable string """
    ver = _version.Version("1.2.3.4.foo", True, 5)
    assert_equals(str(ver), "1.2.3.4.foo-dev-r5")

    ver = _version.Version("1.2.3.4.foo", False, 5)
    assert_equals(str(ver), "1.2.3.4.foo")

    ver = _version.Version("1.2.3.4.foo\xe9", False, 5)
    assert_equals(str(ver), "1.2.3.4.foo\xe9")


def test_unicode():
    """ Version accepts and produces reasonable unicode """
    ver = _version.Version("1.2.3.4.foo", True, 5)
    assert_equals(unicode(ver), u"1.2.3.4.foo-dev-r5")

    ver = _version.Version(u"1.2.3.4.\xe9", True, 5)
    assert_equals(unicode(ver), u"1.2.3.4.\xe9-dev-r5")

    ver = _version.Version(u"1.2.3.4.\xe9", False, 5)
    assert_equals(unicode(ver), u"1.2.3.4.\xe9")

    # utf-8 is detected
    ver = _version.Version("1.2.3.4.\xc3\xa9", False, 5)
    assert_equals(unicode(ver), u"1.2.3.4.\xe9")


def test_repr():
    """ Version produces reasonable repr """
    ver = _version.Version("1.2.3.4.foo", True, 5)
    assert_equals(
        repr(ver),
        "tdi._version.Version('1.2.3.4.foo', is_dev=True, revision=5)"
    )

    ver = _version.Version("1.2.3.4.foo", False, 5)
    assert_equals(
        repr(ver),
        "tdi._version.Version('1.2.3.4.foo', is_dev=False, revision=5)"
    )

    ver = _version.Version("1.2.3.4.foo\xe9", True, 5)
    assert_equals(
        repr(ver),
        "tdi._version.Version('1.2.3.4.foo\\xe9', is_dev=True, revision=5)"
    )
