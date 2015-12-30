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
 Tests for tdi.markup.soup.encoder
===================================

Tests for tdi.markup.soup.encoder
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals, assert_true
from .... import _util as _test

from tdi.markup.soup import encoder as _encoder

U = _test.uni  # pylint: disable = invalid-name


@_test.multi_impl(globals(), _encoder, name='impl')
def test_soup_encoder_init(impl):
    """ SoupEncoder initializes properly """
    result = _encoder.SoupEncoder('FOO')

    assert_true(isinstance(result, _encoder.SoupEncoder))
    tresult = type(result)

    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.c._tdi_impl.SoupEncoder' if impl == 'c' else
                  'tdi.markup.soup.encoder.SoupEncoder')
    assert_equals(result.encoding, 'FOO')
