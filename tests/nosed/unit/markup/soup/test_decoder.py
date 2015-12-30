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
 Tests for tdi.markup.soup.decoder
===================================

Tests for tdi.markup.soup.decoder
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_equals, assert_true, assert_raises
from .... import _util as _test

from tdi.markup.soup import decoder as _decoder

U = _test.uni  # pylint: disable = invalid-name


@_test.multi_impl(globals(), _decoder, name='impl')
def test_html_decoder_init(impl):
    """ HTMLDecoder initializes properly """
    result = _decoder.HTMLDecoder('FOO')

    assert_true(isinstance(result, _decoder.HTMLDecoder))
    tresult = type(result)

    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.c._tdi_impl.HTMLDecoder' if impl == 'c' else
                  'tdi.markup.soup.decoder.HTMLDecoder')
    assert_equals(result.encoding, 'FOO')


@_test.multi_impl(globals(), _decoder)
def test_html_decoder_normalize():
    """ HTMLDecoder().normalize() works as expected """
    name = U(r'Xo\xC92')

    inst = _decoder.HTMLDecoder('FOO')

    assert_equals(inst.normalize(name), U(r'xo\xe92'))


@_test.multi_impl(globals(), _decoder)
def test_html_decoder_decode_strict():
    """ HTMLDecoder().decode() decodes strict """
    inst = _decoder.HTMLDecoder('latin-1')

    result = inst.decode(
        U(r"-&gt;Andr\xe9&#xe9;&eacute;&eacute &amp; Malo")
        .encode('latin-1')
    )

    assert_equals(result, U(r'->Andr\xe9\xe9\xe9&eacute & Malo'))


@_test.multi_impl(globals(), _decoder)
def test_html_decoder_decode_strict_error():
    """ HTMLDecoder().decode() errors on strict decoding """
    inst = _decoder.HTMLDecoder('utf-8')

    with assert_raises(UnicodeError):
        inst.decode(
            U(r"-&gt;Andr\xe9&#xe9;&eacute;&eacute &amp; Malo")
            .encode('latin-1')
        )


@_test.multi_impl(globals(), _decoder)
def test_html_decoder_decode_replace():
    """ HTMLDecoder().decode() accepts different error handlers """
    inst = _decoder.HTMLDecoder('utf-8')

    result = inst.decode(
        U(r"-&gt;Andr\xe9&#xe9;&eacute;&eacute &amp; Malo")
        .encode('latin-1'),
        'replace'
    )

    assert_equals(result, U(r'->Andr\ufffd\xe9\xe9&eacute & Malo'))


@_test.multi_impl(globals(), _decoder)
def test_html_decoder_attribute_strict_unquoted():
    """ HTMLDecoder().attribute() works strict, unquoted """
    value = U(r"An*d'r&apos;\xe9 &quot;Malo").replace('*', r'\\\"')
    inst = _decoder.HTMLDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'''An*d'r'\xe9 "Malo''').replace('*', r'\\\"'))


@_test.multi_impl(globals(), _decoder)
def test_html_decoder_attribute_strict_quoted():
    """ HTMLDecoder().attribute() works strict, quoted (") """
    value = U(r'"An*d' r"'" r'r&apos;\xe9 &quot;Malo"').replace('*', r'\\\"')
    inst = _decoder.HTMLDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'''An*d'r'\xe9 "Malo''').replace('*', r'\\\"'))


@_test.multi_impl(globals(), _decoder)
def test_html_decoder_attribute_strict_quoted2():
    """ HTMLDecoder().attribute() works strict, quoted (') """
    value = U(r"'An*d'r&apos;\xe9 &quot;Malo'").replace('*', r'\\\"')
    inst = _decoder.HTMLDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'''An*d'r'\xe9 "Malo''').replace('*', r'\\\"'))


@_test.multi_impl(globals(), _decoder, name='impl')
def test_xml_decoder_init(impl):
    """ XMLDecoder initializes properly """
    result = _decoder.XMLDecoder('FOO')

    assert_true(isinstance(result, _decoder.XMLDecoder))
    tresult = type(result)

    assert_equals("%s.%s" % (tresult.__module__, tresult.__name__),
                  'tdi.c._tdi_impl.XMLDecoder' if impl == 'c' else
                  'tdi.markup.soup.decoder.XMLDecoder')
    assert_equals(result.encoding, 'FOO')


@_test.multi_impl(globals(), _decoder)
def test_xml_decoder_normalize():
    """ XMLDecoder().normalize() works as expected """
    name = U(r'Xo\xC92')

    inst = _decoder.XMLDecoder('FOO')

    assert_true(inst.normalize(name) is name)


@_test.multi_impl(globals(), _decoder)
def test_xml_decoder_decode_strict():
    """ XMLDecoder().decode() decodes strict """
    inst = _decoder.XMLDecoder('latin-1')

    result = inst.decode(
        U(r"-&gt;Andr\xe9&#xe9;&eacute;&eacute &amp; Malo")
        .encode('latin-1')
    )

    assert_equals(result, U(r'->Andr\xe9\xe9\xe9&eacute & Malo'))


@_test.multi_impl(globals(), _decoder)
def test_xml_decoder_decode_strict_error():
    """ XMLDecoder().decode() errors on strict decoding """
    inst = _decoder.XMLDecoder('utf-8')

    with assert_raises(UnicodeError):
        inst.decode(
            U(r"-&gt;Andr\xe9&#xe9;&eacute;&eacute &amp; Malo")
            .encode('latin-1')
        )


@_test.multi_impl(globals(), _decoder)
def test_xml_decoder_decode_replace():
    """ XMLDecoder().decode() accepts different error handlers """
    inst = _decoder.XMLDecoder('utf-8')

    result = inst.decode(
        U(r"-&gt;Andr\xe9&#xe9;&eacute;&eacute &amp; Malo")
        .encode('latin-1'),
        'replace'
    )

    assert_equals(result, U(r'->Andr\ufffd\xe9\xe9&eacute & Malo'))


@_test.multi_impl(globals(), _decoder)
def test_xml_decoder_attribute_strict_unquoted():
    """ XMLDecoder().attribute() works strict, unquoted """
    value = U(r"An*d'r&apos;\xe9 &quot;Malo").replace('*', r'\\\"')
    inst = _decoder.XMLDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'''An*d'r'\xe9 "Malo''').replace('*', r'\\\"'))


@_test.multi_impl(globals(), _decoder)
def test_xml_decoder_attribute_strict_quoted():
    """ XMLDecoder().attribute() works strict, quoted (") """
    value = U(r'"An*d' r"'" r'r&apos;\xe9 &quot;Malo"').replace('*', r'\\\"')
    inst = _decoder.XMLDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'''An*d'r'\xe9 "Malo''').replace('*', r'\\\"'))


@_test.multi_impl(globals(), _decoder)
def test_xml_decoder_attribute_strict_quoted2():
    """ XMLDecoder().attribute() works strict, quoted (') """
    value = U(r"'An*d'r&apos;\xe9 &quot;Malo'").replace('*', r'\\\"')
    inst = _decoder.XMLDecoder('latin-1')

    result = inst.attribute(value.encode('latin-1'))

    assert_equals(result, U(r'''An*d'r'\xe9 "Malo''').replace('*', r'\\\"'))
