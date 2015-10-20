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

========================
 Output Encoder Classes
========================

This module provides output encoding logic.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from ... import interfaces as _interfaces


class TextEncoder(object):
    """ Encoder for text output """
    __implements__ = [_interfaces.EncoderInterface]

    def __init__(self, encoding):
        """
        Initialization

        :Parameters:
          `encoding` : ``str``
            The target encoding
        """
        self.encoding = encoding

    def starttag(self, name, attr, closed):
        """ :See: `EncoderInterface` """
        return (closed and "[[%s]]" or "[%s]") % (' '.join([name] + [
            value is not None and "%s=%s" % (key, value) or key
            for key, value in attr
        ]))

    def endtag(self, name):
        """ :See: `EncoderInterface` """
        return "[/%s]" % name

    def name(self, name):
        """ :See: `EncoderInterface` """
        if isinstance(name, unicode):
            return name.encode(self.encoding, 'strict')
        return name

    def attribute(self, value):
        """ :See: `EncoderInterface` """
        if isinstance(value, unicode):
            value = (
                value
                .replace(u'"', u'\\"')
                .encode(self.encoding, 'strict')
            )
        else:
            value = value.replace('"', '\\"')
        return '"%s"' % value

    def content(self, value):
        """ :See: `EncoderInterface` """
        if isinstance(value, unicode):
            return (
                value
                .encode(self.encoding, 'strict')
            )
        return value

    def encode(self, value):
        """ :See: `EncoderInterface` """
        return value.encode(self.encoding, 'strict')

    def escape(self, value):
        """ :See: `EncoderInterface` """
        return value.replace('[', '[]')


from ... import c
c = c.load('impl')
if c is not None:
    TextEncoder = c.TextEncoder  # noqa
del c
