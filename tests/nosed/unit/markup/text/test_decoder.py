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
 Tests for tdi.markup.text.decoder
===================================

Tests for tdi.markup.text.decoder
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals, assert_true, assert_raises
from .... import _util as _test

from tdi.markup.text import decoder as _decoder

U = _test.uni  # pylint: disable = invalid-name


@_test.multi_impl(globals(), _decoder, name='impl')
def test_decoder_init(impl):
    """ TextDecoder initializes properly """
    result = _decoder.TextDecoder('FOO')

    assert_true(isinstance(result, _decoder.TextDecoder))
    tresult = type(result)

    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.c._tdi_impl.TextDecoder' if impl == 'c' else
                  'tdi.markup.text.decoder.TextDecoder')
    assert_equals(result.encoding, 'FOO')


@_test.multi_impl(globals(), _decoder)
def test_decoder_normalize():
    """ TextDecoder().normalize() works as expected """
    name = 'x' * 200

    inst = _decoder.TextDecoder('FOO')

    assert_true(inst.normalize(name) is name)


@_test.multi_impl(globals(), _decoder)
def test_decoder_decode_strict():
    """ TextDecoder().decode() decodes strict """
    inst = _decoder.TextDecoder('latin-1')

    result = inst.decode(U(r"Andr\xe9 Malo").encode('latin-1'))

    assert_equals(result, U(r'Andr\xe9 Malo'))


@_test.multi_impl(globals(), _decoder)
def test_decoder_decode_strict_error():
    """ TextDecoder().decode() errors on strict decoding """
    inst = _decoder.TextDecoder('utf-8')

    with assert_raises(UnicodeError):
        inst.decode(U(r"Andr\xe9 Malo").encode('latin-1'))


@_test.multi_impl(globals(), _decoder)
def test_decoder_decode_replace():
    """ TextDecoder().decode() accepts different error handlers """
    inst = _decoder.TextDecoder('utf-8')

    result = inst.decode(U(r"Andr\xe9 Malo").encode('latin-1'), 'replace')

    assert_equals(result, U(r'Andr\ufffd Malo'))


@_test.multi_impl(globals(), _decoder)
def test_decoder_attribute_strict_unquoted():
    """ TextDecoder().attribute() works strict, unquoted """
    value = U(r"An*dr\xe9 Malo").replace('*', r'\\\"')
    inst = _decoder.TextDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'An*dr\xe9 Malo').replace('*', r'\"'))


@_test.multi_impl(globals(), _decoder)
def test_decoder_attribute_strict_quoted():
    """ TextDecoder().attribute() works strict, quoted (") """
    value = U(r'"An*dr\xe9 Malo"').replace('*', r'\\\"')
    inst = _decoder.TextDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'An*dr\xe9 Malo').replace('*', r'\"'))


@_test.multi_impl(globals(), _decoder)
def test_decoder_attribute_strict_quoted2():
    """ TextDecoder().attribute() works strict, quoted (') """
    value = U(r"'An*dr\xe9 Malo'").replace('*', r"\\\'")
    inst = _decoder.TextDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'An*dr\xe9 Malo').replace('*', r"\'"))
