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

================
 DTD Collection
================

This module provides a collection of DTD query classes to be used with
the soup parser.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from ... import interfaces as _interfaces


class HTMLDTD(object):
    """
    Query class for the HTML DTD

    :IVariables:
      `_cdata` : ``dict``
        Dict of CDATA elements (for speed lookup)

      `_optional` : ``dict``
        Dict of optional elements (for speed lookup)

      `_empty` : ``dict``
        Dict of empty elements (for speed lookup)
    """
    __implements__ = [_interfaces.DTDInterface]

    #: List of known empty elements
    #:
    #: :Type: ``tuple``
    _EMPTY = ('app', 'area', 'base', 'basefont', 'bgsound', 'br', 'col',
              'command', 'embed', 'frame', 'hr', 'img', 'input', 'isindex',
              'keygen', 'link', 'meta', 'nextid', 'param', 'sound', 'source',
              'spacer', 'track', 'wbr')

    #: List of CDATA elements
    #:
    #: plaintext has been specified differently over time. Sometimes it's
    #: finishable, sometimes not. I let it be finishable here. You shouldn't
    #: use it anyway.
    #:
    #: :Type: ``tuple``
    _CDATA = ('listing', 'plaintext', 'script', 'style', 'textarea', 'xmp')

    # helper
    _intable = ('caption', 'col', 'colgroup', 'tbody', 'thead', 'tfoot')

    #: List of elements with optional end tag. This list consists
    #: of (name, forbidden-list) pairs.
    #:
    #: :Type: ``tuple``
    _OPTIONAL = tuple({
        # pylint: disable = bad-whitespace

        'html':     ('html',),
        'head':     ('html', 'body', 'head',),
        'body':     ('html', 'body', 'head',),
        'li':       ('li',),
        'dt':       ('dt', 'dd',),
        'dd':       ('dt', 'dd',),
        'p':        ('address', 'article', 'aside', 'blockquote', 'body',
                     'dd', 'dir', 'div', 'dl', 'dt', 'fieldset', 'footer',
                     'form', 'frame', 'frameset', 'h1', 'h2', 'h3', 'h4',
                     'h5', 'h6', 'head', 'header', 'hgroup', 'hr', 'html',
                     'isindex', 'layer', 'li', 'listing', 'map', 'marquee',
                     'menu', 'multicol', 'nav', 'noframes', 'ol', 'p',
                     'plaintext', 'pre', 'section', 'table', 'td', 'th',
                     'tr', 'ul', 'xmp') + _intable,
        'rt':       ('rt', 'rp',),
        'rp':       ('rt', 'rp',),
        'optgroup': ('optgroup',),
        'option':   ('option', 'optgroup',),
        'colgroup': _intable + ('td', 'th', 'tr',),
        'caption':  _intable + ('td', 'th', 'tr',),
        'thead':    _intable,
        'tbody':    _intable,
        'tfoot':    _intable,
        'tr':       _intable + ('tr',),
        'td':       _intable + ('td', 'th', 'tr',),
        'th':       _intable + ('td', 'th', 'tr',),
    }.items())
    del _intable

    def __init__(self):
        """ Initialization """
        dict_ = dict
        optional = dict_([
            (name, dict_([
                (item, None) for item in forbidden
            ]).__contains__)
            for name, forbidden in self._OPTIONAL
        ]).get
        if self.__class__ == HTMLDTD:
            self.cdata = dict_([
                (item, None) for item in self._CDATA
            ]).__contains__
            self.empty = empty = dict_([
                (item, None) for item in self._EMPTY
            ]).__contains__

            def nestable(outer, inner):
                """ :See: `tdi.interfaces.DTDInterface.nestable` """
                opt = optional(outer)
                if opt is not None:
                    return not opt(inner)
                elif empty(outer):
                    return False
                return True
            self.nestable = nestable
        else:
            self._empty = dict_([
                (item, None) for item in self._EMPTY
            ]).__contains__
            self._cdata = dict_([
                (item, None) for item in self._CDATA
            ]).__contains__
            self._optional = optional

    def cdata(self, name):
        """ :See: `tdi.interfaces.DTDInterface.cdata` """
        # pylint: disable = method-hidden

        return self._cdata(name)

    def nestable(self, outer, inner):
        """ :See: `tdi.interfaces.DTDInterface.nestable` """
        # pylint: disable = method-hidden

        opt = self._optional(outer)
        if opt is not None:
            return not opt(inner)
        elif self._empty(outer):
            return False

        return True

    def empty(self, name):
        """ :See: `tdi.interfaces.DTDInterface.empty` """
        # pylint: disable = method-hidden

        return self._empty(name)


class XMLDTD(object):
    """
    XML DTD query class

    This class effectively defines every wellformed XML valid.
    """
    __implements__ = [_interfaces.DTDInterface]

    # pylint: disable = unused-argument

    def cdata(self, name):
        """ :See: `DTDInterface` """
        return False

    def nestable(self, outer, inner):
        """ :See: `DTDInterface` """
        return True

    def empty(self, name):
        """ :See: `DTDInterface` """
        return False
