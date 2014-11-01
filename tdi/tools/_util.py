# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2006 - 2014
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
 Tool Utilities
================

Tool Utilities.
"""
from __future__ import absolute_import

__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import encodings as _encodings


def _make_norm_enc():
    """ Make encoding normalizer """
    isinstance_, unicode_, str_ = isinstance, unicode, str
    normalize = _encodings.normalize_encoding
    aliases = _encodings.aliases.aliases.get
    get_alias = lambda x: aliases(x, x)

    def norm_enc(encoding):  # pylint: disable = W0621
        """ Return normalized unaliased encoding name """
        if not isinstance_(encoding, unicode_):
            encoding = str_(encoding).decode('latin-1')
        return get_alias(normalize(encoding.lower()))

    return norm_enc

norm_enc = _make_norm_enc()
