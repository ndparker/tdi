# -*- coding: ascii -*-
#
# Copyright 2006, 2007, 2008, 2009, 2010, 2011
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
=================
 Factory Caching
=================

Factory Caching.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"


def _copy_doc(func):
    """
    Copy docstring

    :Parameters:
      `func` : ``callable``
        The method's function
    """
    from tdi import factory as _factory
    method = getattr(_factory.Factory, func.__name__, None)
    if method is not None:
        func.__doc__ = method.__doc__


class MemoizedFactory(object):
    """
    Wrapper for providing template factory memoization keys

    :IVariables:
      `_factory` : `tdi.factory.Factory`
        Factory
    """

    def __init__(self, factory):
        """
        Initialization

        :Parameters:
          `factory` : `tdi.factory.Factory`
            Factory
        """
        self._factory = factory

    def replace(self, autoupdate=None, eventfilters=None, streamfilters=None,
                default_eventfilters=None, default_streamfilters=None,
                overlay_eventfilters=None, overlay_streamfilters=None,
                overlay_default_eventfilters=None,
                overlay_default_streamfilters=None, default_encoding=None,
                memoizer=None):
        """ Create factory with replaced parameters """
        # pylint: disable = R0913
        # (too many arguments)

        return self.__class__(self._factory.replace(
            autoupdate=autoupdate,
            eventfilters=eventfilters,
            streamfilters=streamfilters,
            default_eventfilters=default_eventfilters,
            default_streamfilters=default_streamfilters,
            overlay_eventfilters=overlay_eventfilters,
            overlay_streamfilters=overlay_streamfilters,
            overlay_default_eventfilters=overlay_default_eventfilters,
            overlay_default_streamfilters=overlay_default_streamfilters,
            default_encoding=default_encoding,
            memoizer=memoizer,
        ))
    _copy_doc(replace)

    def from_file(self, filename, encoding=None, key=None):
        """ Build template from file """
        if key is None:
            key = filename
        return self._factory.from_file(filename, encoding=encoding,
            key=key
        )
    _copy_doc(from_file)

    def from_stream(self, stream, encoding=None, filename=None, mtime=None,
                    opener=None, key=None):
        """ Build template from stream """
        if key is None:
            key = filename
        return self._factory.from_stream(stream, encoding=encoding,
            filename=filename, mtime=mtime, opener=opener,
            key=key
        )
    _copy_doc(from_stream)

    def from_opener(self, opener, filename, encoding=None, key=None):
        """ Build template from stream opener """
        if key is None:
            key = filename
        return self._factory.from_opener(opener, filename, encoding=encoding,
            key=key
        )
    _copy_doc(from_opener)

    def from_string(self, data, encoding=None, filename=None, mtime=None,
                    key=None):
        """ Build template from string """
        if key is None:
            key = filename
        return self._factory.from_string(data, encoding=encoding,
            filename=filename, mtime=mtime,
            key=key
        )
    _copy_doc(from_string)

    def from_files(self, names, encoding=None, basedir=None, key=None):
        """ Load templates from files and overlay them """
        if key is None:
            key = (basedir,) + tuple(names)
        return self._factory.from_files(names, encoding=encoding,
            basedir=basedir,
            key=key
        )
    _copy_doc(from_files)

    def from_streams(self, streams, encoding=None, streamopen=None,
                     key=None):
        """ Load templates from streams and overlay them """
        if key is None:
            key = tuple(streams)
            try:
                hash(key)
            except TypeError:
                key = None
        return self._factory.from_streams(streams, encoding=encoding,
            streamopen=streamopen,
            key=key
        )
    _copy_doc(from_streams)
