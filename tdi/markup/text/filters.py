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
 Text Filter Classes
=====================

Filters for text templates.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import re as _re

from tdi import filters as _filters


class EncodingDetectFilter(_filters.BaseEventFilter):
    """ Extract template encoding and pass it properly to the builder """

    #: Regex matcher to match encoding declarations
    #:
    #: :Type: ``callable``
    _PI_MATCH = _re.compile(r'''
        \[\? \s*
        [eE][nN][cC][oO][dD][iI][nN][gG] (?:\s+|\s*=\s*) (?P<enc>[^=\s?]+)
        \s* \?\]$
    ''', _re.X).match

    def handle_pi(self, data):
        """
        Extract encoding from PI instruction

        Here's a sample for the expected format::

          [? encoding latin-1 ?]

        The event is passed to the builder nevertheless.

        :See: `BuildingListenerInterface`
        """
        match = self._PI_MATCH(data)
        if match:
            self.builder.handle_encoding(match.group('enc'))
        self.builder.handle_pi(data)
