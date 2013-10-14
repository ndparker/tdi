# -*- coding: ascii -*-
#
# Copyright 2010 - 2013
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
  #filters.html.load =
  #filters.html.overlay =
  #filters.html.template =
  #filters.xml.load =
  #filters.xml.overlay =
  #filters.xml.template=

  # load + overlay Filters are lists of (event) filter factories, for example
  #
  #filters.html.load =
  #  tdi.tools.html.MinifyFilter
  #
  # template filters work on the final template object
"""
__docformat__ = "restructuredtext en"
__author__ = u"Andr\xe9 Malo"

import errno as _errno
import itertools as _it
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading

try:
    from wtf import services as _wtf_services
except ImportError:
    _wtf_services = None

from tdi import factory as _factory
from tdi import factory_memoize as _factory_memoize
from tdi import interfaces as _interfaces
from tdi import model_adapters as _model_adapters
from tdi import util as _util
from tdi.markup import factory as _markup_factory
from tdi.tools import htmlform as _htmlform


def _resource():
    """ Load resource service """
    from __svc__.wtf import resource
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

    def getlist(self, name): # pylint: disable = E0202
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        return self.param.multi(name)


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
    """

    def __init__(self, locations, autoreload=False, filters=None):
        """
        Initialization

        :Parameters:
          `locations` : iterable
            Resource locations (``['token', ...]``)

          `autoreload` : ``bool``
            Automatically reload templates?

          `filters` : ``dict``
            Filter factories to apply
        """
        self._dirs = list(_it.chain(*[_resource()[location]
            for location in locations]))

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
            def load(names):
                """ Actual loader """
                res = factory.from_streams(names, streamopen=streamopen)
                for item in post_load or ():
                    res = item(res)
                return res
            return load

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
                _util.load_dotted, filter(None, opt(filters, args) or ())
            ) or None

        self.html = loader('html',
            post_load=load('html', 'template'),
            eventfilters=load('html', 'load'),
            overlay_eventfilters=load('html', 'overlay'),
        )
        self.xml = loader('xml',
            post_load=load('xml', 'template'),
            eventfilters=load('xml', 'load'),
            overlay_eventfilters=load('xml', 'overlay'),
        )

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
                if e[0] == _errno.ENOENT:
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
        def load_html(response):
            """ Response factory for ``load_html`` """
            # pylint: disable = W0613
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
                response, global_template.html, "render_html"
            )
        def pre_render_html(response):
            """ Response factory for ``pre_render_html`` """
            return self._render_factory(
                response, global_template.html, "pre_render_html", pre=True
            )
        def load_xml(response):
            """ Response factory for ``load_html`` """
            # pylint: disable = W0613
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
                response, global_template.xml, "render_xml"
            )
        def pre_render_xml(response):
            """ Response factory for ``pre_render_xml`` """
            return self._render_factory(
                response, global_template.xml, "pre_render_xml", pre=True,
            )

        self.env = {
            'wtf.response.load_html': load_html,
            'wtf.response.render_html': render_html,
            'wtf.response.pre_render_html': pre_render_html,
            'wtf.response.load_xml': load_xml,
            'wtf.response.render_xml': render_xml,
            'wtf.response.pre_render_xml': pre_render_xml,
        }

    def _render_factory(self, response, template_loader, func_name,
                        pre=False):
        """
        Response factory for ``render_html/xml``

        :Parameters:
          `response` : ``wtf.response.Response``
            The response object

          `template_loader` : ``callable``
            Template loader function

          `func_name` : ``str``
            Name of the render function (only for introspection)

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
            if kwargs:
                raise TypeError("Unrecognized kwargs: %r" % kwargs.keys())

            tpl = template_loader(names)
            encoding = tpl.encoding
            response.content_type(charset=encoding)
            if pre and prerender is not None:
                return [tpl.render_string(
                    prerender, startnode=startnode,
                    adapter=_model_adapters.RenderAdapter.for_prerender,
                )]
            return [tpl.render_string(
                model, startnode=startnode, prerender=prerender,
            )]
        try:
            render_func.__name__ = func_name # pylint: disable = W0622
        except TypeError: # python 2.3 doesn't allow changing names
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
        # pylint: disable = W0613
        self._global =  GlobalTemplate(
            config.tdi.locations,
            config.tdi('autoreload', False),
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
