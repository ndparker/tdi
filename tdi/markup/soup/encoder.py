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
 Output Encoder Classes
========================

This module provides output encoding logic.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

from tdi import interfaces as _interfaces


class SoupEncoder(object):
    """ Encoder for HTML/XML output """
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
        return "<%s%s>" % (' '.join([name] + [
            value is not None and "%s=%s" % (key, value) or key
            for key, value in attr
        ]), closed and ' /' or '')

    def endtag(self, name):
        """ :See: `EncoderInterface` """
        return "</%s>" % name

    def name(self, name):
        """ :See: `EncoderInterface` """
        if isinstance(name, unicode):
            return name.encode(self.encoding, 'strict')
        return name

    def attribute(self, value):
        """ :See: `EncoderInterface` """
        if isinstance(value, unicode):
            value = (value
                .replace(u'&', u'&amp;')
                .replace(u'<', u'&lt;')
                .replace(u'>', u'&gt;')
                .replace(u'"', u'&quot;')
                .encode(self.encoding, 'xmlcharrefreplace')
            )
        else:
            value = (value
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
            )

        return '"%s"' % value

    def content(self, value):
        """ :See: `EncoderInterface` """
        if isinstance(value, unicode):
            return (value
                .replace(u'&', u'&amp;')
                .replace(u'<', u'&lt;')
                .replace(u'>', u'&gt;')
                .encode(self.encoding, 'xmlcharrefreplace')
            )
        return (value
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
        )

    def encode(self, value):
        """ :See: `EncoderInterface` """
        return value.encode(self.encoding, 'xmlcharrefreplace')

    def escape(self, value):
        """ :See: `EncoderInterface` """
        return value


from tdi import c
c = c.load('impl')
if c is not None:
    SoupEncoder = c.SoupEncoder
del c
