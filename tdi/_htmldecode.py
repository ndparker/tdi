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

==============
 HTML Decoder
==============

HTML Decoder.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import re as _re

from . import _htmlentities


def _make_decode():
    """ Make decoder """
    from . import c
    c = c.load('impl')
    if c is not None:
        return c.htmldecode

    sub = _re.compile(ur'&([^& \t\n\r\f;]*);').sub
    unicode_, unichr_, str_, int_ = unicode, unichr, str, int
    isinstance_ = isinstance
    default_entities = dict(_htmlentities.htmlentities)

    def decode(value, encoding='latin-1', errors='strict', entities=None):
        """
        Decode HTML encoded text

        :Parameters:
          `value` : ``basestring``
            HTML content to decode

          `encoding` : ``str``
            Unicode encoding to be applied before value is being processed
            further. If value is already a unicode instance, the encoding is
            ignored. If omitted, 'latin-1' is applied (because it can't fail
            and maps bytes 1:1 to unicode codepoints).

          `errors` : ``str``
            Error handling, passed to .decode() and evaluated for entities.
            If the entity name or character codepoint could not be found or
            not be parsed then the error handler has the following semantics:

            ``strict`` (or anything different from the other tokens below)
                A ``ValueError`` is raised.

            ``ignore``
                The original entity is passed through

            ``replace``
                The character is replaced by the replacement character
                (U+FFFD)

          `entities` : ``dict``
            Entity name mapping (unicode(name) -> unicode(value)). If
            omitted or ``None``, the `HTML5 entity list`_ is applied.

            .. _HTML5 entity list: http://www.w3.org/TR/html5/
               syntax.html#named-character-references

        :Return: The decoded content
        :Rtype: ``unicode``
        """
        # pylint: disable = redefined-outer-name

        if not isinstance_(value, unicode_):
            value = str_(value).decode(encoding, errors)
        if entities is None:
            entities = default_entities

        def subber(match):
            """ Substituter """
            name = match.group(1)
            if not name.startswith(u'#'):
                try:
                    return entities[name]
                except KeyError:
                    pass
            else:
                if name.startswith(u'#x') or name.startswith(u'#X'):
                    base = 16
                    name = name[2:]
                else:
                    base = 10
                    name = name[1:]
                try:
                    return unichr_(int_(name, base))
                except (ValueError, TypeError, OverflowError):
                    pass

            if errors == 'ignore':
                return match.group(0)
            elif errors == 'replace':
                return u'\ufffd'
            else:
                raise ValueError(
                    "Unresolved entity %r" % (match.group(0),)
                )

        return sub(subber, value)
    return decode

decode = _make_decode()
