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
===============================
 Default Soup Template Factory
===============================

Default Soup Template Factory.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"
__all__ = ['html', 'xml', 'text']

from tdi import factory as _factory

class _soup(object):
    from tdi.markup.soup import (
        builder,
        decoder,
        encoder,
        filters,
        parser,
    )

class _text(object):
    from tdi.markup.text import (
        builder,
        decoder,
        encoder,
        filters,
        parser,
    )


html = _factory.Factory(
    parser=_soup.parser.DEFAULT_PARSER.html,
    builder=_soup.builder.SoupBuilder,
    encoder=_soup.encoder.SoupEncoder,
    decoder=_soup.decoder.HTMLDecoder,
    default_eventfilter_list=(_soup.filters.EncodingDetectFilter,),
)

xml = _factory.Factory(
    parser=_soup.parser.DEFAULT_PARSER.xml,
    builder=_soup.builder.SoupBuilder,
    encoder=_soup.encoder.SoupEncoder,
    decoder=_soup.decoder.XMLDecoder,
    default_encoding='utf-8',
    default_eventfilter_list=(_soup.filters.EncodingDetectFilter,),
)


text = _factory.Factory(
    parser=_text.parser.TextParser,
    builder=_text.builder.TextBuilder,
    encoder=_text.encoder.TextEncoder,
    decoder=_text.decoder.TextDecoder,
    default_encoding='utf-8',
    default_eventfilter_list=(_text.filters.EncodingDetectFilter,),
)
