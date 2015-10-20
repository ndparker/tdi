# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2006 - 2015
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
 Soup Filter Classes
=====================

Filters for soup templates.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import re as _re

from ... import filters as _filters


def _make_parse_content_type():
    """
    Make content type parser

    :Return: parse_content_type
    :Rtype: ``callable``
    """
    # These are a bit more lenient than RFC 2045.
    tokenres = r'[^\000-\040()<>@,;:\\"/[\]?=]+'
    qcontent = r'[^\000\\"]'
    qsres = r'"%(qc)s*(?:\\"%(qc)s*)*"' % {'qc': qcontent}
    valueres = r'(?:%(token)s|%(quoted-string)s)' % {
        'token': tokenres, 'quoted-string': qsres,
    }

    typere = _re.compile(
        r'\s*([^;/\s]+/[^;/\s]+)((?:\s*;\s*%(key)s\s*=\s*%(val)s)*)\s*$' % {
            'key': tokenres, 'val': valueres,
        }
    )
    pairre = _re.compile(r'\s*;\s*(%(key)s)\s*=\s*(%(val)s)' % {
        'key': tokenres, 'val': valueres
    })
    stripre = _re.compile(r'\r?\n')

    def _parse_content_type(value):
        """
        Parse a content type

        :Warning: comments are not recognized (yet?)

        :Parameters:
          `value` : ``basestring``
            The value to parse - must be ascii compatible

        :Return: The parsed header (``(value, {key, [value, value, ...]})``)
                 or ``None``
        :Rtype: ``tuple``
        """
        try:
            if isinstance(value, unicode):
                value.encode('ascii')
            else:
                value.decode('ascii')
        except (AttributeError, UnicodeError):
            return None

        match = typere.match(value)
        if not match:
            return None

        parsed = (match.group(1).lower(), {})
        match = match.group(2)
        if match:
            for key, val in pairre.findall(match):
                if val[:1] == '"':
                    val = stripre.sub(r'', val[1:-1]).replace(r'\"', '"')
                parsed[1].setdefault(key.lower(), []).append(val)

        return parsed

    return _parse_content_type

_parse_content_type = _make_parse_content_type()


class EncodingDetectFilter(_filters.BaseEventFilter):
    """ Extract template encoding and pass it properly to the builder """
    __slots__ = ('_normalize', '_meta')

    def __init__(self, builder):
        """ Initialization """
        super(EncodingDetectFilter, self).__init__(builder)
        self._normalize = self.builder.decoder.normalize
        self._meta = self._normalize('meta')

    def handle_starttag(self, name, attr, closed, data):
        """
        Extract encoding from HTML meta element

        Here are samples for the expected formats::

          <meta charset="utf-8"> <!-- HTML5 -->

          <meta http-equiv="Content-Type" content="text/html; charset=utf-8">

        The event is passed to the builder nevertheless.

        :See: `BuildingListenerInterface`
        """
        normalize = self._normalize

        iname = normalize(name)
        if iname == self._meta:
            adict = dict([(normalize(key), val) for key, val in attr])
            value = str((adict.get(normalize('charset')) or ''))
            if value.startswith('"') or value.startswith("'"):
                value = value[1:-1].strip()
            if value:
                self.builder.handle_encoding(value)
            else:
                value = (adict.get(normalize('http-equiv')) or '').lower()
                if value.startswith('"') or value.startswith("'"):
                    value = value[1:-1].strip()
                if value == 'content-type':
                    ctype = adict.get(normalize('content'))
                    if ctype:
                        if ctype.startswith('"') or ctype.startswith("'"):
                            ctype = ctype[1:-1].strip()

                        parsed = _parse_content_type(ctype)
                        if parsed is not None:
                            encoding = parsed[1].get('charset')
                            if encoding:
                                self.builder.handle_encoding(
                                    encoding[0].strip()
                                )

        self.builder.handle_starttag(name, attr, closed, data)

    #: Regex matcher to match xml declarations
    #:
    #: :Type: ``callable``
    _PI_MATCH = _re.compile(r'''
        <\? \s* [xX][mM][lL] \s+ (?P<attr>
            [^"'?]*
            (?:
                (?:
                    "[^"]*"
                  | '[^']*'
                )
                [^"'?]*
            )*
        )
        \s* \?>$
    ''', _re.X).match

    #: Iterator over the matched xml declaration attributes
    #:
    #: :Type: ``callable``
    _PI_ATT_ITER = _re.compile(r'''
        \s*
        (?P<name>[^\s=]*)        # attribute name
        \s*
        =
        (?P<value>               # value
            \s*"[^"]*"
          | \s*'[^']*'
        )
    ''', _re.X).finditer

    def handle_pi(self, data):
        """
        Extract encoding from xml declaration

        Here's a sample for the expected format::

          <?xml version="1.0" encoding="ascii" ?>

        The event is passed to the builder nevertheless.

        :See: `BuildingListenerInterface`
        """
        match = self._PI_MATCH(str(data))
        if match:
            encoding = 'utf-8'  # xml default
            for match in self._PI_ATT_ITER(match.group('attr')):
                key, value = match.group('name', 'value')
                if key or value:
                    if key == 'encoding':
                        value = value.strip()
                        if value.startswith('"') or value.startswith("'"):
                            value = value[1:-1].strip()
                        if value:
                            encoding = value
                        break
                else:
                    break
            self.builder.handle_encoding(encoding)
        self.builder.handle_pi(data)

from ... import c
c = c.load('impl')
if c is not None:
    EncodingDetectFilter = c.SoupEncodingDetectFilter  # noqa
del c
