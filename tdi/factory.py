# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2006 - 2016
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

====================
 Template Factories
====================

Template Factories.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import os as _os
import sys as _sys
try:
    import cStringIO as _string_io
except ImportError:
    import StringIO as _string_io
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

from ._exceptions import TemplateFactoryError
from . import filters as _filters
from . import template as _template
from . import _util


class Loader(object):
    """
    Template loader

    :IVariables:
      `_args` : ``dict``
        Initialization arguments

      `_new_parser` : ``callable``
        Parser factory

      `_streamfilters` : iterable
        List of stream filter factories (``(file, ...)``)

      `_chunksize` : ``int``
        Chunk size when reading templates
    """

    def __init__(self, parser, builder, encoder, decoder,
                 eventfilters=None, streamfilters=None,
                 default_eventfilter_list=None,
                 default_streamfilter_list=None,
                 default_eventfilters=True, default_streamfilters=True,
                 chunksize=None):
        """
        Initialization

        :Parameters:
          `parser` : ``callable``
            Parser factory (takes a builder instance and the decoder,
            returns `ParserInterface`)

          `builder` : ``callable``
            Tree builder factory (takes the `encoder` and the decoder)

          `encoder` : ``callable``
            Encoder factory (takes the target encoding)

          `decoder` : ``callable``
            Decoder factory (takes the source encoding)

          `eventfilters` : iterable
            List of event filter factories
            (``(BuildingListenerInterface, ...)``)

          `streamfilters` : iterable
            List of stream filter factories (``(file, ...)``)

          `default_eventfilter_list` : ``list``
            Default eventfilter list

          `default_streamfilter_list` : ``list``
            Default streamfilter list

          `default_eventfilters` : ``bool``
            Apply default eventfilters (before this list)?

          `default_streamfilters` : ``bool``
            Apply default streamfilters (before this list)?

          `chunksize` : ``int``
            Chunk size when reading templates
        """
        # pylint: disable = too-many-arguments

        self._args = dict(locals())
        del self._args['self']

        default = list(default_streamfilter_list or ())
        if streamfilters is None:
            streamfilters = default
        elif default_streamfilters:
            streamfilters = default + list(streamfilters)
        streamfilters.reverse()
        self._streamfilters = tuple(streamfilters)

        if chunksize is None:
            chunksize = 8192
        self._chunksize = chunksize

        default = tuple(default_eventfilter_list or ())
        if eventfilters is None:
            eventfilters = default
        elif default_eventfilters:
            eventfilters = default + tuple(eventfilters)

        def new_builder():
            """
            Make builder instance

            :Return: Builder instance
            :Rtype: `TreeBuildInterface`
            """
            return builder(encoder, decoder)

        self.builder = new_builder

        def make_parser(filename, encoding):
            """
            Make parser instance

            :Return: Parser and tree returner
            :Rtype: ``tuple``
            """
            this_builder = _filters.FilterFilename(new_builder(), filename)
            for item in eventfilters:
                this_builder = item(this_builder)
            this_builder.handle_encoding(encoding)
            return parser(this_builder), this_builder.finalize

        self._new_parser = make_parser

    @_util.Property
    def args():
        """
        The initialization arguments

        :Type: ``dict``
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = protected-access, missing-docstring

        def fget(self):
            return dict(self._args)
        return locals()

    def persist(self, filename, encoding, opener):
        """
        Create persistent loader (able to reload)

        :Parameters:
          `filename` : ``str``
            Filename in question

          `encoding` : ``str``
            Initial template encoding

          `opener` : ``callable``
            Stream opener, returns stream and mtime

        :Return: A new Reloader instance
        :Rtype: `tdi.factory.Reloader`
        """
        return Reloader(self, filename, encoding, opener)

    def __call__(self, stream, filename, encoding):
        """
        Actually load the template and build the tree

        :Parameters:
          `stream` : ``file``
            The stream to read from

          `filename` : ``str``
            The template filename

          `encoding` : ``str``
            Initial template encoding

        :Return: The tree
        :Rtype: `tdi.nodetree.Root`
        """
        stream = _filters.StreamFilename(stream, filename)
        for item in self._streamfilters:
            stream = item(stream)

        parser, make_tree = self._new_parser(filename, encoding)
        feed, size, read = parser.feed, self._chunksize, stream.read
        while True:
            chunk = read(size)
            if not chunk:
                break
            feed(chunk)
        parser.finalize()
        return make_tree()


class Reloader(object):
    """
    Loader wrapper, configured for a particular template

    :IVariables:
      `_loader` : `Loader`
        Loader instance

      `_filename` : ``str``
        Template name

      `_encoding` : ``str``
        Initial encoding

      `_opener` : ``callable``
        Stream opener
    """
    __slots__ = ('_loader', '_filename', '_encoding', '_opener')

    def __init__(self, loader, filename, encoding, opener):
        """
        Persist loader

        :Parameters:
          `loader` : `Loader`
            Loader instance

          `filename` : ``str``
            Filename in question

          `encoding` : ``str``
            Initial template encoding

          `opener` : ``callable``
            Stream opener, returns stream and mtime

        :Return: persisted loader (takes stream and optional mtime)
        :Rtype: ``callable``
        """
        self._loader = loader
        self._filename = filename
        self._encoding = encoding
        self._opener = opener

    def load(self, mtime=None, force=False):
        """
        Load the template again, if the mtime changed.

        :Parameters:
          `mtime` : any
            modification time of the current template. If omitted or
            ``None``, no mtime evaluation will happen.

          `force` : ``bool``
            Force loading independently from mtime?

        :Return: The template tree and the new tree's mtime. If the template
                 didn't change (determined by mtime evaluation) and loading
                 was not forced - the tree is None.
        :Rtype: ``tuple``
        """
        if force:
            mtime = None
        stream, mtime = self._opener(self._filename, mtime)
        try:
            if stream is None:
                return stream, mtime
            return self._loader(stream, self._filename, self._encoding), mtime
        finally:
            if stream is not None:
                stream.close()

    def check(self, mtime):
        """
        Check the template for modifications, by evaluating mtime.

        :Parameters:
          `mtime` : any
            Known modification time. If ``None``, the return value will
            indicate a change.

        :Return: A tuple of: update available? and the new mtime
        :Rtype: ``tuple``
        """
        return self._opener(self._filename, mtime, check_only=True)


def file_opener(filename, mtime, check_only=False):
    """
    File stream opener

    :Parameters:
      `filename` : ``str``
        Filename

      `mtime` : ``int``
        mtime to check. If it equals the file's mtime, stream is returned as
        ``None``

      `check_only` : ``bool``
        Only check? In this case the returned "stream" is either True (update
        available) or False (mtime didn't change)

    :Return: The stream and its mtime
    :Rtype: ``tuple``
    """
    if check_only:
        try:
            xtime = _os.stat(filename).st_mtime
        except OSError:
            xtime = None
        update = mtime is None or xtime is None or mtime != xtime
        return update, xtime

    stream = open(filename, 'rb')
    try:
        try:
            xtime = _os.fstat(stream.fileno()).st_mtime
        except (OSError, AttributeError):
            xtime = None
        if mtime is not None and xtime is not None and mtime == xtime:
            stream, _ = None, stream.close()  # noqa
        return stream, xtime
    except:  # pylint: disable = bare-except
        e = _sys.exc_info()
        try:
            stream.close()
        finally:
            try:
                raise e[0], e[1], e[2]
            finally:
                del e


def overlay(templates):
    """
    Overlay a list of templates from left to right

    :Parameters:
      `templates` : iterable
        Template list

    :Return: The final template
    :Rtype: `tdi.template.Template`
    """
    templates = list(templates)
    templates.reverse()
    try:
        result = templates.pop()
    except IndexError:
        raise TemplateFactoryError("Need at least one template")
    while templates:
        result = result.overlay(templates.pop())
    return result


#: Global memoization lock
#:
#: :Type: Lock
_global_lock = _threading.Lock()


def _memoize(func):
    """
    Decorate a factory method call to possibly memoize the result

    :Parameters:
      `func` : ``callable``
        Method's function

    :Return: Decorated function
    :Rtype: ``callable``
    """
    name = func.__name__

    def proxy(*args, **kwargs):
        """ Proxy """
        self, key = args[0], kwargs.pop('key', None)
        cache = self._cache  # pylint: disable = protected-access
        if cache is None or key is None:
            return func(*args, **kwargs)
        lock, ckey = getattr(cache, 'lock', None), (name, key)
        if lock is None:
            lock = _global_lock
        lock.acquire()
        try:
            if ckey in cache:
                return cache[ckey]
        finally:
            lock.release()
        res = func(*args, **kwargs)
        lock.acquire()
        try:
            if ckey in cache:
                return cache[ckey]
            else:
                cache[ckey] = res
                return res
        finally:
            lock.release()
    return _util.decorating(func, extra=dict(key=None))(proxy)


class Factory(object):
    """
    Template builder/loader factory

    The method calls are memoized, if:

    - a memoizer is given on instantiation (like ``dict``)
    - a key is supplied to the method (as keyword argument ``key``). The key
      must be hashable. You can wrap an automatic key supplier around the
      factory instance, for example `tdi.factory_memoize.MemoizedFactory`.

    :IVariables:
      `_loader` : `Loader`
        Template loader

      `_autoupdate` : ``bool``
        Should the templates be automatically updated when
        they change?

      `_cache` : `MemoizerInterface`
        Memoizer or ``None``

      `overlay_filters` : ``dict``
        Overlay filters

      `_default_encoding` : ``str``
        Default encoding
    """

    def __init__(self, parser, builder, encoder, decoder,
                 autoupdate=False, eventfilters=None, streamfilters=None,
                 default_eventfilters=True, default_streamfilters=True,
                 default_eventfilter_list=None,
                 default_streamfilter_list=None,
                 overlay_eventfilters=None, overlay_streamfilters=None,
                 overlay_default_eventfilters=True,
                 overlay_default_streamfilters=True,
                 default_encoding='ascii', chunksize=None, memoizer=None):
        """
        Initialization

        :Parameters:
          `parser` : ``callable``
            Parser factory (takes a builder instance and the decoder,
            returns `ParserInterface`)

          `builder` : ``callable``
            Tree builder factory (takes the `encoder` and the decoder)

          `encoder` : ``callable``
            Encoder factory (takes the target encoding)

          `decoder` : ``callable``
            Decoder factory (takes the source encoding)

          `autoupdate` : ``bool``
            Should the templates be automatically updated when
            they change?

          `eventfilters` : iterable
            List of event filter factories
            (``(BuildingListenerInterface, ...)``)

          `streamfilters` : iterable
            List of stream filter factories (``(file, ...)``)

          `default_eventfilters` : ``bool``
            Apply default eventfilters (before this list)?

          `default_streamfilters` : ``bool``
            Apply default streamfilters (before this list)?

          `default_eventfilter_list` : ``iterable``
            List of default eventfilters

          `default_streamfilter_list` : ``iterable``
            List of default streamfilters

          `overlay_eventfilters` : iterable
            List of event filter factories
            (``(BuildingListenerInterface, ...)``) to apply after all
            overlaying being done (right before (pre)rendering)

          `overlay_streamfilters` : iterable
            List of stream filter factories (``(file, ...)``)
            to apply after all overlaying being done (right before
            (pre)rendering)

          `overlay_default_eventfilters` : ``bool``
            Apply default eventfilters (before this list)?

          `overlay_default_streamfilters` : ``bool``
            Apply default streamfilters (before this list)?

          `default_encoding` : ``str``
            Default encoding

          `chunksize` : ``int``
            Chunk size when reading templates

          `memoizer` : `MemoizerInterface`
            Memoizer to use. If omitted or ``None``, memoization is turned
            off.
        """
        # pylint: disable = too-many-arguments

        self._loader = Loader(
            parser=parser,
            decoder=decoder,
            eventfilters=eventfilters,
            streamfilters=streamfilters,
            default_eventfilters=default_eventfilters,
            default_streamfilters=default_streamfilters,
            default_eventfilter_list=list(default_eventfilter_list or ()),
            default_streamfilter_list=list(default_streamfilter_list or ()),
            builder=builder,
            encoder=encoder,
            chunksize=chunksize,
        )
        if overlay_eventfilters is None and overlay_streamfilters is None:
            self.overlay_filters = None
        else:
            self.overlay_filters = dict(
                eventfilters=overlay_eventfilters,
                streamfilters=overlay_streamfilters,
                default_eventfilters=overlay_default_eventfilters,
                default_streamfilters=overlay_default_streamfilters,
            )
        self._autoupdate = autoupdate
        self._cache = memoizer
        self._default_encoding = default_encoding

    def builder(self):
        """
        Return a tree builder instance as configured by this factory

        The purpose of the method is mostly internal. It's used to get the
        builder in order to inspect it.

        :Return: Builder
        :Rtype: `BuilderInterface`
        """
        return self._loader.builder()

    def replace(self, autoupdate=None, eventfilters=None, streamfilters=None,
                default_eventfilters=None, default_streamfilters=None,
                overlay_eventfilters=None, overlay_streamfilters=None,
                overlay_default_eventfilters=None,
                overlay_default_streamfilters=None, default_encoding=None,
                memoizer=None):
        """
        Create a new factory instance with replaced values

        :Parameters:
          `autoupdate` : ``bool``
            Should the templates be automatically updated when
            they change? If omitted or ``None``, the current setting is
            applied.

          `eventfilters` : iterable
            List of event filter factories
            (``(BuildingListenerInterface, ...)``)

          `streamfilters` : iterable
            List of stream filter factories (``(file, ...)``)

          `default_eventfilters` : ``bool``
            Apply default eventfilters (before this list)?

          `default_streamfilters` : ``bool``
            Apply default streamfilters (before this list)?

          `overlay_eventfilters` : iterable
            List of overlay event filter factories
            (``(BuildingListenerInterface, ...)``)

          `overlay_streamfilters` : iterable
            List of overlay stream filter factories (``(file, ...)``)

          `overlay_default_eventfilters` : ``bool``
            Apply overlay default eventfilters (before this list)?

          `overlay_default_streamfilters` : ``bool``
            Apply overlay default streamfilters (before this list)?

          `default_encoding` : ``str``
            Default encoding

          `memoizer` : `MemoizerInterface`
            New memoizer. If omitted or ``None``, the new factory will be
            initialized without memoizing.

        :Return: New factory instance
        :Rtype: `Factory`
        """
        # pylint: disable = too-many-arguments, too-many-branches
        # pylint: disable = unsubscriptable-object, not-a-mapping

        args = self._loader.args
        if autoupdate is None:
            autoupdate = self._autoupdate
        args['autoupdate'] = autoupdate
        if eventfilters is not None:
            args['eventfilters'] = eventfilters
        if default_eventfilters is not None:
            args['default_eventfilters'] = default_eventfilters
        if streamfilters is not None:
            args['streamfilters'] = streamfilters
        if default_streamfilters is not None:
            args['default_streamfilters'] = default_streamfilters

        if self.overlay_filters:
            for key, value in self.overlay_filters.iteritems():
                args['overlay_' + key] = value
        if overlay_eventfilters is not None:
            args['overlay_eventfilters'] = overlay_eventfilters
        if overlay_default_eventfilters is not None:
            args['overlay_default_eventfilters'] = \
                overlay_default_eventfilters
        if overlay_streamfilters is not None:
            args['overlay_streamfilters'] = overlay_streamfilters
        if overlay_default_streamfilters is not None:
            args['overlay_default_streamfilters'] = \
                overlay_default_streamfilters

        if default_encoding is None:
            args['default_encoding'] = self._default_encoding
        else:
            args['default_encoding'] = default_encoding

        if memoizer is not None:
            args['memoizer'] = memoizer

        return self.__class__(**args)

    @_memoize
    def from_file(self, filename, encoding=None, cls=None):
        """
        Build template from file

        :Parameters:
          `filename` : ``str``
            The filename to read the template from

          `encoding` : ``str``
            The initial template encoding. If omitted or ``None``, the default
            encoding is applied.

          `cls` : ``callable``
            result wrapper, takes the resulting template and returns the final
            template. If omitted or ``None``, the result won't be wrapped.
            Note that the wrapped result will be memoized (if memoization is
            enabled).

        :Return: A new `tdi.template.Template` instance
        :Rtype: `tdi.template.Template`

        :Exceptions:
          - `Error` : An error occured while loading the template
          - `IOError` : Error while opening/reading the file
        """
        return self.from_opener(file_opener, filename, encoding=encoding,
                                cls=cls)

    @_memoize
    def from_opener(self, opener, filename, encoding=None, cls=None):
        """
        Build template from stream as returned by stream opener

        :Parameters:
          `opener` : ``callable``
            Stream opener, returns stream and mtime.

          `filename` : ``str``
            "Filename" of the template. It's passed to the opener, so it knows
            what to open.

          `encoding` : ``str``
            Initial template encoding. If omitted or ``None``, the default
            encoding is applied.

          `cls` : ``callable``
            result wrapper, takes the resulting template and returns the final
            template. If omitted or ``None``, the result won't be wrapped.
            Note that the wrapped result will be memoized (if memoization is
            enabled).

        :Return: The new `tdi.template.Template` instance
        :Rtype: `tdi.template.Template`
        """
        if encoding is None:
            encoding = self._default_encoding
        loader = self._loader.persist(filename, encoding, opener)
        tree, mtime = loader.load()
        result = _template.Template(tree, filename, mtime, self, loader)
        if cls is not None:
            result = cls(result)
        if self._autoupdate:
            result = _template.AutoUpdate(result)
        return result

    @_memoize
    def from_stream(self, stream, encoding=None, filename=None, mtime=None,
                    cls=None):
        """
        Build template from stream

        Since the stream is exhausted after reading it, templates created
        using this method cannot be auto-updated. If you want auto-updated
        templates constructed from streams, use `from_opener`.

        :Parameters:
          `stream` : ``file``
            The stream to read from

          `encoding` : ``str``
            Initial template encoding. If omitted or ``None``, the default
            encoding is applied.

          `filename` : ``str``
            Optional fake filename of the template. If not set,
            it's taken from ``stream.name``. If this is not possible,
            it's ``<stream>``.

          `mtime` : ``int``
            Optional fake mtime

          `cls` : ``callable``
            result wrapper, takes the resulting template and returns the final
            template. If omitted or ``None``, the result won't be wrapped.
            Note that the wrapped result will be memoized (if memoization is
            enabled).

        :Return: The new `tdi.template.Template` instance
        :Rtype: `tdi.template.Template`
        """
        if encoding is None:
            encoding = self._default_encoding
        if filename is None:
            try:
                filename = stream.name
            except AttributeError:
                filename = '<stream>'
        tree = self._loader(stream, filename, encoding)
        result = _template.Template(tree, filename, mtime, self, None)
        if cls is not None:
            return cls(result)
        return result

    @_memoize
    def from_string(self, data, encoding=None, filename=None, mtime=None,
                    cls=None):
        """
        Build template from from string

        Templates built using this method cannot be auto-updated, because
        strings are constant.

        :Parameters:
          `data` : ``str``
            The string to process

          `encoding` : ``str``
            The initial template encoding. If omitted or ``None``, the
            default encoding is applied.

          `filename` : ``str``
            Optional fake filename of the template. If not set,
            it's ``<string>``

          `mtime` : ``int``
            Optional fake mtime

          `cls` : ``callable``
            result wrapper, takes the resulting template and returns the final
            template. If omitted or ``None``, the result won't be wrapped.
            Note that the wrapped result will be memoized (if memoization is
            enabled).

        :Return: The new `tdi.template.Template` instance
        :Rtype: `tdi.template.Template`
        """
        if filename is None:
            filename = '<string>'
        return self.from_stream(_string_io.StringIO(data),
                                encoding=encoding, filename=filename,
                                mtime=mtime, cls=cls)

    @_memoize
    def from_files(self, names, encoding=None, basedir=None, cls=None):
        """
        Load templates from files and overlay them

        :Parameters:
          `names` : iterable
            List of filenames, possibly relative to basedir

          `encoding` : ``str``
            Initial template encoding for all files. If omitted or ``None``,
            the default encoding is applied.

          `basedir` : ``basestring``
            Directory, all filenames are relative to. If omitted or ``None``
            the names are applied as-is.

          `cls` : ``callable``
            result wrapper, takes the resulting template and returns the final
            template. If omitted or ``None``, the result won't be wrapped.
            Note that the wrapped result will be memoized (if memoization is
            enabled).

        :Return: The final template
        :Rtype: `tdi.template.Template`
        """
        if basedir is not None:
            names = [_os.path.join(basedir, name) for name in names]
        result = overlay([
            self.from_file(  # pylint: disable = unexpected-keyword-arg
                name, encoding=encoding, key=name
            )
            for name in names
        ])
        if cls is not None:
            return cls(result)
        return result

    @_memoize
    def from_streams(self, streams, encoding=None, streamopen=None, cls=None):
        """
        Load templates from streams and overlay them

        :Parameters:
          `streams` : iterable
            List of items identifying the streams. If `streamopen` is omitted
            or ``None`` the streams are assumed to be regular filenames.

          `encoding` : ``str``
            Initial template encoding for all streams. If omitted or ``None``,
            the default encoding is applied.

          `streamopen` : ``callable``
            Function taking the passed item (of streams) and returning a
            tuple:

            - the stream specification. This itself is either a 2-tuple or a
              3-tuple. A 2-tuple contains a stream opener and a filename
              and is passed to `from_opener`. A 3-tuple contains the open
              stream, the filename and the mtime and is passed to
              `from_stream`. (filename and mtime may be ``None``.)
            - the memoization key, may be ``None``

            If omitted or ``None``, the items are assumed to be file names.

          `cls` : ``callable``
            result wrapper, takes the resulting template and returns the final
            template. If omitted or ``None``, the result won't be wrapped.
            Note that the wrapped result will be memoized (if memoization is
            enabled).

        :Return: The final template
        :Rtype: `tdi.template.Template`
        """
        if streamopen is None:
            streamopen = lambda x: ((file_opener, x), x)

        def tpls():
            """ Get templates """
            for item in streams:
                tup, key = streamopen(item)
                if len(tup) == 3:
                    # pylint: disable = unbalanced-tuple-unpacking
                    stream, filename, mtime = tup
                    try:
                        tpl = self.from_stream(  # noqa pylint: disable = unexpected-keyword-arg
                            stream, encoding=encoding, filename=filename,
                            mtime=mtime, key=key,
                        )
                    finally:
                        stream.close()  # pylint: disable = no-member
                    yield tpl
                else:
                    opener, filename = tup
                    yield self.from_opener(  # noqa pylint: disable = unexpected-keyword-arg
                        opener, filename, encoding=encoding, key=key,
                    )
        result = overlay(tpls())
        if cls is not None:
            return cls(result)
        return result
