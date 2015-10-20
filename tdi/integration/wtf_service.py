# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2010 - 2015
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

=============
 TDI Service
=============

This module implements the tdi template locating and caching service.

Configuration
~~~~~~~~~~~~~

::

  [resources]
  # example: templates directory parallel to the app package.
  template_site = app:../templates

  [tdi]
  # locations is a ResourceService location
  locations = templates_site
  #autoreload = False
  #require_scopes = False
  #require_methods = False
  #filters.html.load =
  #filters.html.overlay =
  #filters.html.template =
  #filters.xml.load =
  #filters.xml.overlay =
  #filters.xml.template=
  #filters.text.load =
  #filters.text.overlay =
  #filters.text.template=

  # load + overlay Filters are lists of (event) filter factories, for example
  #
  #filters.html.load =
  #  tdi.tools.html.MinifyFilter
  #
  # template filters work on the final template object
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import errno as _errno
import itertools as _it
import os as _os
import posixpath as _posixpath
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

try:
    from wtf import services as _wtf_services
except ImportError:
    _wtf_services = None

from .. import factory as _factory
from .. import factory_memoize as _factory_memoize
from .. import interfaces as _interfaces
from .. import model_adapters as _model_adapters
from ..markup import factory as _markup_factory
from ..tools import htmlform as _htmlform


def _load_dotted(name):
    """
    Load a dotted name

    The dotted name can be anything, which is passively resolvable (i.e.
    without the invocation of a class to get their attributes or the like).
    For example, `name` could be 'tdi.integration.wtf_service._load_dotted'
    and would return this very function. It's assumed that the first part of
    the `name` is always is a module.

    :Parameters:
      `name` : ``str``
        The dotted name to load

    :Return: The loaded object
    :Rtype: any

    :Exceptions:
     - `ImportError` : A module in the path could not be loaded
    """
    components = name.split('.')
    path = [components.pop(0)]
    obj = __import__(path[0])
    while components:
        comp = components.pop(0)
        path.append(comp)
        try:
            obj = getattr(obj, comp)
        except AttributeError:
            __import__('.'.join(path))
            try:
                obj = getattr(obj, comp)
            except AttributeError:
                raise ImportError('.'.join(path))

    return obj


def _resource():
    """ Load resource service """
    from __svc__.wtf import resource  # pylint: disable = import-error
    return resource


class RequestParameterAdapter(object):
    """
    HTMLForm parameter adapter from request.param

    :IVariables:
      `param` : ``wtf.request.Request.param``
        request.param
    """
    __implements__ = [_htmlform.ParameterAdapterInterface]

    def __init__(self, param):
        """
        Initialization

        :Parameters:
          `param` : ``wtf.request.Request.param``
            request.param
        """
        self.param = param
        if self.__class__ is RequestParameterAdapter:
            self.getlist = param.multi

    def getfirst(self, name, default=None):
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        if name in self.param:
            return self.param[name]
        return default

    def getlist(self, name):  # pylint: disable = method-hidden
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        return self.param.multi(name)


class DirectoryTemplateLister(object):
    """ Directory Template Lister """

    #: Default list of directory names to ignore
    #:
    #: :Type: ``tuple``
    DEFAULT_IGNORE = ('.svn', 'CVS', '.git', '.bzr', '.hg')

    def __init__(self, directories, extensions, ignore=None):
        """
        Initialization

        :Parameters:
          `directories` : ``iterable``
            List of base directories to scan

          `extensions` : ``iterable``
            List of extensions to consider

          `ignore` : ``iterable``
            List of directory names to ignore. If omitted or ``None``,
            `DEFAULT_IGNORE` is applied.
        """
        self._dirs = tuple(_it.imap(str, directories))
        self._ext = tuple(_it.imap(str, extensions or ()))
        self._ci = _os.path.normcase('aA') != 'aA'
        if ignore is None:
            ignore = self.DEFAULT_IGNORE
        if self._ci:
            self._ignore = frozenset((
                _os.path.normcase(item) for item in (ignore or ())
            ))
        else:
            self._ignore = frozenset(ignore or ())

    def __call__(self):
        """
        Walk the directories and yield all template names

        :Return: Iterator over template names
        :Rtype: ``iterable``
        """
        # pylint: disable = too-many-branches

        seen = set()
        if _os.path.sep == '/':
            norm = lambda p: p
        else:
            norm = lambda p: p.replace(_os.path.sep, '/')

        for base in self._dirs:
            baselen = len(_os.path.join(base, ''))
            reldir = lambda x, b=baselen: x[b:]

            def onerror(_):
                """ Error handler """
                raise
            for dirpath, dirs, files in _os.walk(base, onerror=onerror):
                # fixup directories to recurse
                if self._ignore:
                    newdirs = []
                    for dirname in dirs:
                        if self._ci:
                            if _os.path.normcase(dirname) in self._ignore:
                                continue
                        elif dirname in self._ignore:
                            continue
                        newdirs.append(dirname)
                    if len(newdirs) != len(dirs):
                        dirs[:] = newdirs

                # find names
                dirpath = reldir(dirpath)
                for name in files:
                    if not name.endswith(self._ext):
                        continue
                    if dirpath:
                        name = _posixpath.join(norm(dirpath), name)
                    if name in seen:
                        continue
                    yield name


class _Memoizer(dict):
    """ Memoizer storage """
    __implements__ = [_interfaces.MemoizerInterface]

    def __init__(self, *args, **kwargs):
        """ Initialize """
        super(_Memoizer, self).__init__(*args, **kwargs)
        self.lock = _threading.Lock()


class GlobalTemplate(object):
    """
    Actual global template service object

    :IVariables:
      `_dirs` : ``list``
        Template locations resolved to directories

      `autoreload` : ``bool``
        Automatically reload templates?

      `require_scopes` : ``bool``
        Require all scopes?

      `require_methods` : ``bool``
        Require all render methods?
    """

    def __init__(self, locations, autoreload=False, require_scopes=False,
                 require_methods=False, filters=None):
        """
        Initialization

        :Parameters:
          `locations` : iterable
            Resource locations (``['token', ...]``)

          `autoreload` : ``bool``
            Automatically reload templates?

          `require_scopes` : ``bool``
            Require all scopes?

          `require_methods` : ``bool``
            Require all render methods?

          `filters` : ``dict``
            Filter factories to apply
        """
        self._dirs = list(_it.chain(*[
            _resource()[location] for location in locations
        ]))
        self.autoreload = autoreload
        self.require_scopes = require_scopes
        self.require_methods = require_methods

        def streamopen(name):
            """ Stream opener """
            # while getting the stream and closing it immediately seems
            # silly...
            # the logic in self.stream() looks for the file in more than one
            # directory and needs to try to open it in order to check if it's
            # possible to open. However, if we want to autoreload our
            # templates in TDI, TDI doesn't need an open stream, but a
            # function that can open the stream (the so called stream opener)
            # so it (TDI) can re-open the stream any time.
            stream, filename = self.stream(name)
            stream.close()
            return (_factory.file_opener, filename), filename

        def loader(which, post_load=None, **kwargs):
            """ Template loader """
            kwargs['autoupdate'] = autoreload
            kwargs['memoizer'] = _Memoizer()
            factory = _factory_memoize.MemoizedFactory(
                getattr(_markup_factory, which).replace(**kwargs)
            )
            sfactory = factory.replace(overlay_eventfilters=[])

            def load(names):
                """ Actual loader """
                res = factory.from_streams(names, streamopen=streamopen)
                for item in post_load or ():
                    res = item(res)
                return res

            def single(name):
                """ Single file loader """
                return sfactory.from_opener(*streamopen(name)[0])
            return load, single

        def opt(option, args):
            """ Find opt """
            for arg in args:
                try:
                    option = option[arg]
                except (TypeError, KeyError):
                    return None
            return [unicode(opt).encode('utf-8') for opt in option]

        def load(*args):
            """ Actually load factories """
            return map(
                _load_dotted, filter(None, opt(filters, args) or ())
            ) or None

        self.html, self.html_file = loader(
            'html',
            post_load=load('html', 'template'),
            eventfilters=load('html', 'load'),
            overlay_eventfilters=load('html', 'overlay'),
        )
        self.xml, self.xml_file = loader(
            'xml',
            post_load=load('xml', 'template'),
            eventfilters=load('xml', 'load'),
            overlay_eventfilters=load('xml', 'overlay'),
        )
        self.text, self.text_file = loader(
            'text',
            post_load=load('text', 'template'),
            eventfilters=load('text', 'load'),
            overlay_eventfilters=load('text', 'overlay'),
        )

    def lister(self, extensions, ignore=None):
        """
        Create template lister from our own config

        :Parameters:
          `extensions` : ``iterable``
            List of file extensions to consider (required)

          `ignore` : ``iterable``
            List of (simple) directory names to ignore. If omitted or
            ``None``, a default list is applied
            (`DirectoryTemplateLister.DEFAULT_IGNORE`)

        :Return: a template lister
        :Rtype: ``callable``
        """
        return DirectoryTemplateLister([
            rsc.resolve('.').filename for rsc in self._dirs
        ], extensions, ignore=ignore)

    def stream(self, name, mode='rb', buffering=-1, blockiter=0):
        """
        Locate file in the template directories and open a stream

        :Parameters:
          `name` : ``str``
            The relative filename

          `mode` : ``str``
            The opening mode

          `buffering` : ``int``
            buffering spec

          `blockiter` : ``int``
            Iterator mode
            (``1: Line, <= 0: Default chunk size, > 1: This chunk size``)

        :Return: The resource stream
        :Rtype: ``wtf.app.services.resources.ResourceStream``

        :Exceptions:
          - `IOError` : File not found
        """
        for location in self._dirs:
            try:
                loc = location.resolve(name)
                return loc.open(
                    mode=mode, buffering=buffering, blockiter=blockiter
                ), loc.filename
            except IOError, e:
                if e.args[0] == _errno.ENOENT:
                    continue
                raise
        raise IOError(_errno.ENOENT, name)


class ResponseFactory(object):
    """
    Response hint factory collection

    :IVariables:
      `_global` : `GlobalTemplate`
        The global service
    """

    def __init__(self, global_template):
        """
        Initialization

        :Parameters:
          `global_template` : `GlobalTemplate`
            The global template service
        """
        def adapter(model):
            """ Adapter factory """
            return _model_adapters.RenderAdapter(
                model,
                requiremethods=global_template.require_methods,
                requirescopes=global_template.require_scopes,
            )

        def load_html(response):  # pylint: disable = unused-argument
            """ Response factory for ``load_html`` """
            def load_html(*names):
                """
                Load TDI template

                :Parameters:
                  `names` : ``tuple``
                    The template names. If there's more than one name
                    given, the templates are overlayed.

                :Return: The TDI template
                :Rtype: ``tdi.template.Template``
                """
                return global_template.html(names)
            return load_html

        def render_html(response):
            """ Response factory for ``render_html`` """
            return self._render_factory(
                response, global_template.html, adapter,
                "render_html", 'text/html'
            )

        def pre_render_html(response):
            """ Response factory for ``pre_render_html`` """
            return self._render_factory(
                response, global_template.html, adapter,
                "pre_render_html", 'text/html', pre=True
            )

        def load_xml(response):  # pylint: disable = unused-argument
            """ Response factory for ``load_xml`` """
            def load_xml(*names):
                """
                Load TDI template

                :Parameters:
                  `names` : ``tuple``
                    The template names. If there's more than one name
                    given, the templates are overlayed.

                :Return: The TDI template
                :Rtype: ``tdi.template.Template``
                """
                return global_template.xml(names)
            return load_xml

        def render_xml(response):
            """ Response factory for ``render_xml`` """
            return self._render_factory(
                response, global_template.xml, adapter,
                "render_xml", 'text/xml'
            )

        def pre_render_xml(response):
            """ Response factory for ``pre_render_xml`` """
            return self._render_factory(
                response, global_template.xml, adapter,
                "pre_render_xml", 'text/xml', pre=True,
            )

        def load_text(response):  # pylint: disable = unused-argument
            """ Response factory for ``load_text`` """
            def load_text(*names):
                """
                Load TDI template

                :Parameters:
                  `names` : ``tuple``
                    The template names. If there's more than one name
                    given, the templates are overlayed.

                :Return: The TDI template
                :Rtype: ``tdi.template.Template``
                """
                return global_template.text(names)
            return load_text

        def render_text(response):
            """ Response factory for ``render_text`` """
            return self._render_factory(
                response, global_template.text, adapter,
                "render_text", 'text/plain'
            )

        def pre_render_text(response):
            """ Response factory for ``pre_render_text`` """
            return self._render_factory(
                response, global_template.text, adapter,
                "pre_render_text", 'text/plain', pre=True,
            )

        self.env = {
            'wtf.response.load_html': load_html,
            'wtf.response.render_html': render_html,
            'wtf.response.pre_render_html': pre_render_html,
            'wtf.response.load_xml': load_xml,
            'wtf.response.render_xml': render_xml,
            'wtf.response.pre_render_xml': pre_render_xml,
            'wtf.response.load_text': load_text,
            'wtf.response.render_text': render_text,
            'wtf.response.pre_render_text': pre_render_text,
        }

    def _render_factory(self, response, template_loader, adapter, func_name,
                        content_type_, pre=False):
        """
        Response factory for ``render_html/xml/text``

        :Parameters:
          `response` : ``wtf.response.Response``
            The response object

          `template_loader` : ``callable``
            Template loader function

          `adapter` : ``callable``
            render adapter factory

          `func_name` : ``str``
            Name of the render function (only for introspection)

          `content_type_` : ``str``
            Default content type

          `pre` : ``bool``
            Prerender only?

        :Return: The render callable
        :Rtype: ``callable``
        """
        def render_func(model, *names, **kwargs):
            """
            Simplified TDI invocation

            The following keyword arguments are recognized:

            ``startnode`` : ``str``
                The node to render. If omitted or ``None``, the whole
                template is rendered.
            ``prerender`` : any
                Prerender-Model to apply
            ``content_type`` : ``str``
                Content type to set. If omitted, the default content type
                will be set. If ``None``, the content type won't be set.

            :Parameters:
              `model` : any
                The model instance

              `names` : ``tuple``
                The template names. If there's more than one name
                given, the templates are overlayed.

              `kwargs` : ``dict``
                Additional keyword parameters

            :Return: Iterable containing the rendered template
            :Rtype: ``iterable``

            :Exceptions:
              - `Exception` : Anything what happened during rendering
            """
            startnode = kwargs.pop('startnode', None)
            prerender = kwargs.pop('prerender', None)
            content_type = kwargs.pop('content_type', content_type_)
            if kwargs:
                raise TypeError("Unrecognized kwargs: %r" % kwargs.keys())

            tpl = template_loader(names)
            if content_type is not None:
                encoding = tpl.encoding
                response.content_type(content_type, charset=encoding)
            if pre and prerender is not None:
                return [tpl.render_string(
                    prerender, startnode=startnode,
                    adapter=_model_adapters.RenderAdapter.for_prerender,
                )]
            return [tpl.render_string(
                model,
                adapter=adapter, startnode=startnode, prerender=prerender,
            )]
        try:
            render_func.__name__ = func_name
        except TypeError:  # python 2.3 doesn't allow changing names
            pass
        return render_func


class Middleware(object):
    """
    Template middleware

    :IVariables:
      `_func` : ``callable``
        Next WSGI handler

      `_env` : ``dict``
        Environment update
    """

    def __init__(self, global_template, func):
        """
        Initialization

        :Parameters:
          `global_template` : `GlobalTemplate`
            The global template service

          `func` : ``callable``
            WSGI callable to wrap
        """
        self._func = func
        self._env = ResponseFactory(global_template).env

    def __call__(self, environ, start_response):
        """
        Middleware handler

        :Parameters:
          `environ` : ``dict``
            WSGI environment

          `start_response` : ``callable``
            Start response callable

        :Return: WSGI response iterable
        :Rtype: ``iterable``
        """
        environ.update(self._env)
        return self._func(environ, start_response)


class TDIService(object):
    """
    Template service

    :IVariables:
      `_global` : `GlobalTemplate`
        The global service
    """
    if _wtf_services is not None:
        __implements__ = [_wtf_services.ServiceInterface]

    def __init__(self, config, opts, args):
        """ Initialization """
        # pylint: disable = unused-argument

        self._global = GlobalTemplate(
            config.tdi.locations,
            config.tdi('autoreload', False),
            config.tdi('require_scopes', False),
            config.tdi('require_methods', False),
            config.tdi('filters', None),
        )

    def shutdown(self):
        """ :See: ``wtf.services.ServiceInterface.shutdown`` """
        pass

    def global_service(self):
        """ :See: ``wtf.services.ServiceInterface.global_service`` """
        return 'tdi', self._global

    def middleware(self, func):
        """ :See: ``wtf.services.ServiceInterface.middleware`` """
        return Middleware(self._global, func)
