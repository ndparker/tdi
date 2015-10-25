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

===========================
 Tests for tdi.tools._util
===========================

Tests for tdi.tools._util.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals, assert_raises

from tdi.tools import _util


def test_norm_enc_unicode():
    """ norm_enc() works with unicode """
    result = _util.norm_enc(u"LATIN1")

    assert_equals(result, 'latin_1')


def test_norm_enc_str():
    """ norm_enc() works with str """
    result = _util.norm_enc("uTf8")

    assert_equals(result, 'utf_8')


def test_norm_enc_unknown():
    """ norm_enc() works with unknown encodings """
    result = _util.norm_enc("xx-writt\xe9n-KLINGON")

    assert_equals(result, 'xx_writt_n_klingon')


def test_norm_enc_error():
    """ norm_enc() raises UnicodeError with non-latin-1 encodings """
    with assert_raises(UnicodeError):
        _util.norm_enc(u"No \u20acuro")
