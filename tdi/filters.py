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
=========================
 Template Filter Classes
=========================

This module provides the base classes and concrete implementations for
filters.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"


class BaseStreamFilter(object):
    """
    Base stream filter class, which actually passes everything unfiltered

    :IVariables:
      `_stream` : ``file``
        The decorated stream
    """

    def __init__(self, stream):
        """
        Initialization

        :Parameters:
          `stream` : ``file``
            The stream to decorate
        """
        self._stream = stream

    def __getattr__(self, name):
        """
        Delegate unknown symbols to the next stream (downwards)

        :Parameters:
          `name` : ``str``
            The symbol to look up

        :Return: The requested symbol
        :Rtype: any

        :Exceptions:
          - `AttributeError` : The symbol was not found
        """
        return getattr(self._stream, name)


class StreamFilename(BaseStreamFilter):
    """
    Provide filename for upchain stream filters

    :IVariables:
      `filename` : ``str``
        The provided filename
    """

    def __init__(self, stream, filename):
        """
        Initialization

        :Parameters:
          `stream` : ``stream``
            The next stream layer

          `filename` : ``str``
            The filename to provide
        """
        super(StreamFilename, self).__init__(stream)
        self.filename = filename


class BaseEventFilter(object):
    """
    Base event filter class, which actually passes everything unfiltered

    Override the event handlers you need.

    :See: `BuildingListenerInterface`

    :IVariables:
      `builder` : `BuildingListenerInterface`
        The next level builder
    """
    __slots__ = ('builder',)

    def __init__(self, builder):
        """
        Store the next level builder

        :Parameters:
          `builder` : `BuildingListenerInterface`
            The next level builder
        """
        self.builder = builder

    def __getattr__(self, name):
        """
        Delegate unknown symbols to the next level builder (upwards)

        :Parameters:
          `name` : ``str``
            The symbol to look up

        :Return: The requested symbol
        :Rtype: any

        :Exceptions:
          - `AttributeError` : The symbol was not found
        """
        return getattr(self.builder, name)


from tdi import c
c = c.load('impl')
if c is not None:
    BaseEventFilter = c.BaseEventFilter
del c


class FilterFilename(BaseEventFilter):
    """
    Provide the filename for down-chain filters

    :IVariables:
      `filename` : ``str``
        The provided filename
    """

    def __init__(self, builder, filename):
        """
        Initialization

        :Parameters:
          `builder` : `BuildingListenerInterface`
            The next level builder

          `filename` : ``str``
            The filename to provide
        """
        super(FilterFilename, self).__init__(builder)
        self.filename = filename
