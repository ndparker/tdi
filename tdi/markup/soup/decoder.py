# -*- coding: ascii -*-
#
# Copyright 2013
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
=====================
 Soup Input Decoders
=====================

Soup Input Decoders.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

from tdi import _htmldecode as _htmldecode
from tdi import interfaces as _interfaces


class HTMLDecoder(object):
    """
    Decoder for (X)HTML input

    :IVariables:
      `encoding` : ``str``
        Character encoding
    """
    __implements__ = [_interfaces.DecoderInterface]

    def __init__(self, encoding):
        """
        Initialization

        :Parameters:
          `encoding` : ``str``
            Encoding
        """
        self.encoding = encoding

    def normalize(self, name):
        """ :See: `DecoderInterface` """
        return name.lower()

    def decode(self, value, errors='strict'):
        """ :See: `DecoderInterface` """
        return _htmldecode.decode(value, self.encoding, errors=errors)

    def attribute(self, value, errors='strict'):
        """ :See: `DecoderInterface` """
        if value.startswith('"') or value.startswith("'"):
            value = value[1:-1]
        return _htmldecode.decode(value, self.encoding, errors=errors)


class XMLDecoder(object):
    """
    Decoder for XML input

    :IVariables:
      `encoding` : ``str``
        Character encoding
    """
    __implements__ = [_interfaces.DecoderInterface]

    def __init__(self, encoding):
        """
        Initialization

        :Parameters:
          `encoding` : ``str``
            Character encoding
        """
        self.encoding = encoding

    def normalize(self, name):
        """ :See: `DecoderInterface` """
        return name

    def decode(self, value, errors='strict'):
        """ :See: `DecoderInterface` """
        return _htmldecode.decode(value, self.encoding, errors=errors)

    def attribute(self, value, errors='strict'):
        """ :See: `DecoderInterface` """
        if value.startswith('"') or value.startswith("'"):
            value = value[1:-1]
        return _htmldecode.decode(value, self.encoding, errors=errors)


from tdi import c
c = c.load('impl')
if c is not None:
    HTMLDecoder, XMLDecoder = c.HTMLDecoder, c.XMLDecoder
del c
