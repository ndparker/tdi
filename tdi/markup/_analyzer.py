# -*- coding: ascii -*-
#
# Copyright 2006 - 2013
# Andr\xe9 Malo or his licensors, as applicable
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
========================
 Template Builder Logic
========================

This module provides the logic to build a nodetree out of parser
events.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import re as _re

from tdi._exceptions import TemplateAttributeError
from tdi._exceptions import TemplateAttributeEmptyError
from tdi import interfaces as _interfaces


class AttributeAnalyzer(object):
    """
    Attribute analyzer

    :IVariables:
      `attribute` : ``str``
        The attribute name

      `scope` : ``str``
        The scope attribute name

      `_overlay` : ``str``
        The overlay attribute name

      `_removeattr` : ``bool``
        Should `attribute` be removed from the starttag?
    """
    __implements__ = [_interfaces.AttributeAnalyzerInterface]

    #: Regex matcher for valid tdi attributes
    #:
    #: :Type: ``callable``
    _IDMATCH = _re.compile(ur'''
        -$ |
        (?P<flags>(?:
            :|[+-]|\*|
            :[+-]|:\*|[+-]:|[+-]\*|\*:|\*[+-]|
            :[+-]\*|:\*[+-]|[+-]:\*|[+-]\*:|\*:[+-]|\*[+-]:
        )?)
        (?P<name>[A-Za-z][A-Za-z\d_]*)$
    ''', _re.X).match

    #: Regex matcher for valid tdi:overlay attributes
    #:
    #: :Type: ``callable``
    _OVMATCH = _re.compile(ur'''
        (?P<flags>(?:[-+][<>]?|[<>][+-]?)?)
        (?P<name>[A-Za-z][A-Za-z\d_]*)$
    ''', _re.X).match

    #: Regex matcher for valid tdi:scope attributes
    #:
    #: :Type: ``callable``
    _SCMATCH = _re.compile(ur'''
        (?P<flags>(?:[+-]=?|=[+-]?)?)
        (?P<name>(?:[A-Za-z][A-Za-z\d_]*(?:\.[A-Za-z][A-Za-z\d_]*)*)?)$
    ''', _re.X).match

    #: Default tdi attribute name
    #:
    #: :Type: ``str``
    _DEFAULT_ATTRIBUTE = 'tdi'

    #: Default overlay attribute name
    #:
    #: :Type: ``str``
    _DEFAULT_OVERLAY = 'tdi:overlay'

    #: Default scope attribute name
    #:
    #: :Type: ``str``
    _DEFAULT_SCOPE = 'tdi:scope'

    #: Default value for removing the tdi attribute
    #:
    #: :Type: ``bool``
    _DEFAULT_REMOVEATTR = True

    def __init__(self, decoder, attribute=None, overlay=None, scope=None,
                 removeattribute=None, hidden=None):
        """
        Initialization

        :Parameters:
          `attribute` : ``str``
            The special tdi attribute name

          `overlay` : ``str``
            The overlay attribute name

          `scope` : ``str``
            The scope attribute name

          `removeattribute` : ``bool``
            Should `attribute` be removed from the starttag?

          `hidden` : ``bool``
            The default +- flag value. True: Tags are hidden, False:
            Tags are kept. If omitted or ``None``, it's false.
        """
        if attribute is None:
            attribute = self._DEFAULT_ATTRIBUTE
        self.attribute = decoder.normalize(attribute)
        if overlay is None:
            overlay = self._DEFAULT_OVERLAY
        self._overlay = decoder.normalize(overlay)
        if scope is None:
            scope = self._DEFAULT_SCOPE
        self.scope = decoder.normalize(scope)
        if removeattribute is None:
            removeattribute = self._DEFAULT_REMOVEATTR
        self._removeattr = bool(removeattribute)
        self._hidden = bool(hidden)
        self._decoder = decoder
        self._decode_attr = decoder.attribute
        self._normalize = decoder.normalize

    def _parse_attr(self, name, value, matcher):
        """
        Parse attribute value

        :Parameters:
          `name` : ``str``
            Name of the attribute (used for error messages)

          `value` : ``str``
            Raw attribute value (maybe ``None``, but it raises an error,
            because there's some information expected here!)

          `matcher` : ``callable``
            Matcher, expected to return a match object or ``None``.

        :Return: flags and name
        :Rtype: ``tuple`` (``(str, str)``)
        """
        if value is None:
            raise TemplateAttributeError(
                "Invalid short %s attribute" % (name,)
            )
        value = self._decode_attr(value).strip()
        if not value:
            raise TemplateAttributeEmptyError("Empty %s attribute" % (name,))
        return self._parse(name, value, matcher)

    def _parse(self, name, value, matcher):
        """
        Parse value

        :Parameters:
          `name` : ``str``
            Name of the attribute (used for error messages)

          `value` : ``str``
            Raw attribute value (maybe ``None``, but it raises an error,
            because there's some information expected here!)

          `matcher` : ``callable``
            Matcher, expected to return a match object or ``None``.

        :Return: flags and name
        :Rtype: ``tuple`` (``(str, str)``)
        """
        match = matcher(value)
        if match is None:
            raise TemplateAttributeError(
                "Invalid %s attribute %r" % (name, value)
            )
        def uni2str(value):
            """ Simple None-aware encoder """
            if value is None:
                return None
            return value.encode(self._decoder.encoding)
        flags, name = map(uni2str, match.group('flags', 'name'))
        if name is not None:
            if '+' in flags:
                flags = flags.replace('+', '')
            elif self._hidden and '-' not in flags:
                flags += '-'
        return flags, name

    def __call__(self, attr, name=''):
        """
        Analyze attributes

        :Parameters:
          `attr` : sequence
            (key, value) list of attributes. value may be ``None``

          `name` : ``str``
            Name of the tag. If set and containing a value, it's additionally
            considered being equal to a TDI attribute.

        :Return: Either ``None`` if there's nothing special or a tuple of:
                 tdi name, tdi flags, (possibly) reduced attributes, overlay
                 info, scope info
        :Rtype: ``tuple``
        """
        normalize, reduced, special = self._normalize, [], {}
        attribute, overlay, scope = wanted = (
            self.attribute, self._overlay, self.scope
        )
        remove = self._removeattr

        for key, value in attr:
            nkey = normalize(key)
            if nkey in wanted:
                special[nkey] = value
                if remove:
                    continue
            reduced.append((key, value))

        result = {}
        # Scope
        if scope in special:
            result['scope'] = self._parse_attr(
                scope, special[scope], self._SCMATCH,
            )

        # Overlay
        if overlay in special:
            result['overlay'] = self._parse_attr(
                overlay, special[overlay], self._OVMATCH,
            )

        # TDI
        if name:
            nflags, ntdi = self._parse(
                attribute, self._decoder.decode(name), self._IDMATCH
            )
            if not ntdi:
                nflags, ntdi = '-', None
        if attribute in special:
            flags, tdi = self._parse_attr(
                attribute, special[attribute], self._IDMATCH,
            )
            if not tdi:
                flags, tdi = '-', None
            if name and (nflags != flags or ntdi != tdi):
                raise TemplateAttributeError(
                    "%s attribute value %r must equal name" % (
                        attribute, name
                    )
                )
            result['attribute'] = flags, tdi
        elif name:
            result['attribute'] = nflags, ntdi

        return reduced, result


from tdi import c
c = c.load('impl')
if c is not None:
    DEFAULT_ANALYZER = c.AttributeAnalyzer
else:
    DEFAULT_ANALYZER = AttributeAnalyzer
del c
