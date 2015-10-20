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

==================
 Template Objects
==================

Template Objects.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"
__all__ = ['Template', 'OverlayTemplate', 'AutoUpdate']

import sys as _sys

from ._exceptions import (
    Error, TemplateReloadError, AutoUpdateWarning, OverlayError
)
from . import model_adapters as _model_adapters
from . import _util


class Template(object):
    """
    Template class

    :IVariables:
      `filename` : ``str``
        The filename of the template

      `mtime` : any
        Last modification time key (``None`` means n/a)

      `factory` : `Factory`
        Template factory

      `loader` : ``callable``
        Loader

      `_tree` : ``list``
        The nodetree, the overlay-filtered tree and the prerendered tree
    """
    __slots__ = (
        '__weakref__', 'filename', 'mtime', 'factory', 'loader', '_tree'
    )

    @_util.Property
    def tree():
        """
        Prepared node tree

        :Type: `tdi.nodetree.Root`
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = protected-access, missing-docstring

        def fget(self):
            return self._prerender(None, None)
        return locals()

    @_util.Property
    def virgin_tree():
        """
        The node tree without overlay filters

        :Type: `tdi.nodetree.Root`
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = protected-access, missing-docstring

        def fget(self):
            return self._tree[0]
        return locals()

    @_util.Property
    def encoding():
        """
        The template encoding

        :Type: ``str``
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self.virgin_tree.encoder.encoding
        return locals()

    @_util.Property
    def source_overlay_names():
        """
        Source overlay names

        :Type: iterable
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self.virgin_tree.source_overlay_names
        return locals()

    @_util.Property
    def target_overlay_names():
        """
        Target overlay names

        :Type: iterable
        """
        # pylint: disable = no-method-argument, unused-variable
        # pylint: disable = missing-docstring

        def fget(self):
            return self.virgin_tree.target_overlay_names
        return locals()

    def __init__(self, tree, filename, mtime, factory, loader=None):
        """
        Initialization

        :Parameters:
          `tree` : `tdi.nodetree.Root`
            The template tree

          `filename` : ``str``
            Filename of the template

          `mtime` : ``int``
            Last modification time of the template (maybe ``None``)

          `factory` : `Factory`
            Template factory

          `loader` : ``callable``
            Template loader
        """
        self._tree = [tree, None, None]
        self.filename = filename
        self.mtime = mtime
        self.factory = factory
        self.loader = loader

    def __str__(self):
        """
        String representation of the node tree

        :Return: The string representation
        :Rtype: ``str``
        """
        return self.tree.to_string(verbose=False)

    def template(self):
        """ Return a clean template (without any wrapper) """
        return self

    def reload(self, force=False):
        """
        Reload template(s) if possible and needed

        :Parameters:
          `force` : ``bool``
            Force reload? (only if there's a loader present)

        :Return: The reloaded (new) template or self
        :Rtype: `Template`
        """
        if self.loader is not None:
            if force:
                mtime = None
            else:
                mtime = self.mtime
            try:
                tree, mtime = self.loader(mtime)
            except (AttributeError, IOError, OSError, Error), e:
                raise TemplateReloadError(str(e))
            if tree is not None:
                return self.__class__(
                    tree, self.filename, mtime, self.factory, self.loader
                )
        return self

    def update_available(self):
        """
        Check for update

        :Return: Update available?
        :Rtype: ``bool``
        """
        if self.loader is not None:
            return self.loader(self.mtime, check_only=True)[0]
        return False

    def _prepare(self):
        """
        Prepare the tree

        This is a hook, which is run before prerendering is checked and
        executed. By default, this applies the overlay filters.

        :Return: prepared tree
        :Rtype: `tdi.nodetree.Root`
        """
        tree, factory = self._tree[0], self.factory
        if factory.overlay_filters is None:
            return tree
        ffactory = factory.replace(**factory.overlay_filters)
        return ffactory.from_string(''.join(list(tree.render(
            _model_adapters.RenderAdapter.for_prerender(None, attr=dict(
                scope=ffactory.builder().analyze.scope,
                tdi=ffactory.builder().analyze.attribute,
            ))
        ))), encoding=tree.encoder.encoding).virgin_tree

    def _prerender(self, model, adapter):
        """
        Possibly prerender the tree

        :Parameters:
          `model` : any
            Prerender-Model

          `adapter` : `ModelAdapterInterface`
            Prerender-adapter

        :Return: The tree to finally render (either prerendered or not)
        :Rtype: `tdi.nodetree.Root`
        """
        otree, factory = self._tree, self.factory

        # 1st) Prepare the tree (overlay filters and possibly more)
        ftree = otree[1]
        if ftree is None:
            otree[1] = ftree = self._prepare()

        # Without a model *never* return a prerendered tree
        if model is None:
            return ftree

        # 2nd) check if prerendering is actually needed.
        ptree = otree[2]
        if ptree is None:
            version = None
        else:
            version = ptree[1]
        checker = getattr(model, 'prerender_version', None)
        if checker is not None:
            rerender, version = checker(version)
        elif version is not None:
            # The prerendered tree has a version, but the passed
            # prerendermodel does not contain a prerender_version
            # method. This is obviously different from the model used
            # for prerendering (and providing the version) in the first
            # place. We re-pre-render the template and reset the version
            # to None. This seems to be the least surprising way.
            rerender, version = True, None
        else:
            rerender = False
        if ptree is not None and not rerender:
            otree[2] = ptree[0], version
            return ptree[0]

        # 3rd) actually prerender
        filters = getattr(model, 'prerender_filters', None)
        if filters is not None:
            filters = filters().get
            factory = factory.replace(
                eventfilters=filters('eventfilters'),
                default_eventfilters=filters(
                    'default_eventfilters', True
                ),
                streamfilters=filters('streamfilters'),
                default_streamfilters=filters(
                    'default_streamfilters', True
                ),
            )
        if adapter is None:
            adapter = _model_adapters.RenderAdapter.for_prerender
        adapted = adapter(model, attr=dict(
            scope=factory.builder().analyze.scope,
            tdi=factory.builder().analyze.attribute,
        ))
        tree = factory.from_string(
            ''.join(list(ftree.render(adapted))),
            encoding=ftree.encoder.encoding
        ).tree

        otree[2] = tree, version
        return tree

    def render(self, model=None, stream=None, flush=False,
               startnode=None, adapter=None, prerender=None, preadapter=None):
        """
        Render the template into `stream` using `model`

        :Parameters:
          `model` : any
            The model object

          `stream` : ``file``
            The stream to render to. If ``None``, ``sys.stdout`` is
            taken.

          `flush` : ``bool``
            flush after each write? The stream needs a ``flush``
            method in order to do this (If it doesn't have one, `flush`
            being ``True`` is silently ignored)

          `startnode` : ``str``
            Only render this node (and all its children). The node
            is addressed via a dotted string notation, like ``a.b.c`` (this
            would render the ``c`` node.) The notation does not describe a
            strict node chain, though. Between to parts of a node chain may
            be gaps in the tree. The algorithm looks out for the first
            matching node. It does no backtracking and so does not cover all
            branches (yet?), but that works fine for realistic cases :).
            A non-working example would be (searching for a.b.c)::

              *
              +- a
              |  `- b - d
              `- a
                 `- b - c

          `adapter` : ``callable``
            Usermodel adapter factory (takes the model). This
            adapter is responsible for method and attribute resolving in the
            actual user model. If omitted or ``None``, the standard
            `model_adapters.RenderAdapter` is applied.

          `prerender` : any
            Prerender-Model. If omitted or ``None``, no prerendering will
            happen and the original template is rendered.

          `preadapter` : `ModelAdapterInterface`
            Prerender-model adapter factory (takes the model and an attribute
            specification dict). If omitted or ``None``, the standard
            `model_adapters.RenderAdapter.for_prerender` is applied.
        """
        if stream is None:
            stream = _sys.stdout
        if adapter is None:
            adapter = _model_adapters.RenderAdapter
        result = self._prerender(prerender, preadapter).render(
            adapter(model), startnode
        )
        if flush == -1:
            stream.write(''.join(list(result)))
        else:
            write = stream.write
            if flush:
                try:
                    flush = stream.flush
                except AttributeError:
                    pass
                else:
                    for chunk in result:
                        write(chunk)
                        flush()
                    return
            for chunk in result:
                write(chunk)

    def render_string(self, model=None, startnode=None, adapter=None,
                      prerender=None, preadapter=None):
        """
        Render the template as string using `model`

        :Parameters:
          `model` : any
            The model object

          `startnode` : ``str``
            Only render this node (and all its children). See
            `render` for details.

          `adapter` : ``callable``
            Usermodel adapter factory (takes the model). This
            adapter is responsible for method and attribute resolving in the
            actual user model. If omitted or ``None``, the standard
            `model_adapters.RenderAdapter` is applied.

          `prerender` : any
            Prerender-Model

          `preadapter` : `ModelAdapterInterface`
            Prerender-adapter

        :Return: The rendered document
        :Rtype: ``str``
        """
        if adapter is None:
            adapter = _model_adapters.RenderAdapter
        return ''.join(list(self._prerender(prerender, preadapter).render(
            adapter(model), startnode
        )))

    def overlay(self, other):
        """
        Overlay this template with another one

        :Parameters:
          `other` : `Template`
            The template layed over self

        :Return: The combined template
        :Rtype: `Template`
        """
        return OverlayTemplate(self, other)


class OverlayTemplate(Template):
    """ Overlay template representation """
    __slots__ = ('_left', '_right')

    def __init__(self, original, overlay, keep=False):
        """
        Initialization

        :Parameters:
          `original` : `Template`
            Original template

          `overlay` : `Template`
            Overlay template

          `keep` : `Template`
            Keep original templates?
        """
        tree1, tree2 = original.virgin_tree, overlay.virgin_tree
        if tree1.encoder.encoding != tree2.encoder.encoding:
            raise OverlayError("Incompatible templates: encoding mismatch")
        if keep:
            self._left, self._right = original, overlay
        else:
            self._left, self._right = None, None
        filename = "<overlay>"
        if original.mtime is not None and overlay.mtime is not None:
            mtime = max(original.mtime, overlay.mtime)
        else:
            mtime = None
        super(OverlayTemplate, self).__init__(
            tree1.overlay(tree2), filename, mtime, original.factory
        )

    def template(self):
        """ Return a clean template """
        if self._left is not None:
            original = self._left.template()
            overlay = self._right.template()
            if original is not self._left or overlay is not self._right:
                return self.__class__(original, overlay, keep=True)
        return self

    def reload(self, force=False):
        """
        Reload template(s) if possible and needed

        :Parameters:
          `force` : ``bool``
            Force reload (if possible)?

        :Return: The reloaded template or self
        :Rtype: `Template`
        """
        if self._left is not None:
            original = self._left.reload(force=force)
            overlay = self._right.reload(force=force)
            if force or \
                    original is not self._left or overlay is not self._right:
                return self.__class__(original, overlay, keep=True)
        return self

    def update_available(self):
        """
        Check for update

        :Return: Update available?
        :Rtype: ``bool``
        """
        if self._left is not None:
            return (
                self._left.update_available() or
                self._right.update_available()
            )
        return False


class AutoUpdate(object):
    """ Autoupdate wrapper """

    def __init__(self, template, _cb=None):
        """
        Initialization

        :Parameters:
          `template` : `Template`
            The template to autoupdate
        """
        self._template = template.template()
        if _cb is None:
            self._cb = []
        else:
            self._cb = list(_cb)

    def __getattr__(self, name):
        """
        Pass through every request to the original template

        The template is checked before and possibly replaced if it changed.

        :Parameters:
          `name` : ``str``
            Name to lookup

        :Return: The requested value
        :Rtype: any

        :Exceptions:
          - `AttributeError` : not found
        """
        # pylint: disable = protected-access
        return getattr(self.reload(force=False)._template, name)

    def autoupdate_factory(self, new):
        """
        Create new autoupdate wrapper from instance.

        This is needed, when adding template wrappers.

        :Parameters:
          `new` : any
            Template object

        :Return: Autoupdated-wrapped template
        :Rtype: `AutoUpdate`
        """
        return self.__class__(new, _cb=self._cb)

    def autoupdate_register_callback(self, callback):
        """
        Register an autoupdate callback function

        The function will be called, every time a template is reloaded
        automatically. The template is passed as only argument to the callback
        function.

        :Parameters:
          `callback` : ``callable``
            The callback function.
        """
        self._cb.append(callback)

    def overlay(self, other):
        """
        Overlay this template with another one

        :Parameters:
          `other` : `Template`
            The template layed over self

        :Return: The combined template
        :Rtype: `Template`
        """
        return self.__class__(
            OverlayTemplate(self, other, keep=True), _cb=self._cb
        )

    def template(self):
        """ Return a clean template (without any wrapper) """
        return self._template.template()

    def update_available(self):
        """
        Check for update

        :Return: Update available?
        :Rtype: ``bool``
        """
        return self._template.update_available()

    def reload(self, force=False):
        """
        Reload template(s) if possible and needed

        :Parameters:
          `force` : ``bool``
            Force reload (if possible)?

        :Return: The reloaded (new) template or self
        :Rtype: `Template`
        """
        template = self._template
        if force or template.update_available():
            try:
                self._template = template.reload(force=force)
            except TemplateReloadError, e:
                AutoUpdateWarning.emit(
                    'Template autoupdate failed: %s' % str(e)
                )
            for func in list(self._cb):
                func(self)

        return self


class WrappedTemplate(Template):
    """
    Wrapped template base class

    This class can be used to extend the hooks provided by the regular
    template class. Inherit from it and overwrite the methods you need. This
    class just defines the basics.

    :IVariables:
      `_template` : `Template`
        Original template instance

      `_opts` : any
        Options passed via constructor
    """
    __slots__ = ('_opts', '_original')

    def __new__(cls, template, opts=None):
        """
        Construct

        We may return an ``AutoUpdate`` instance here, wrapping the actual
        instance.

        :Parameters:
          `template` : `Template`
            Original template instance

          `opts` : any
            Options
        """
        self = super(WrappedTemplate, cls).__new__(cls)
        factory = getattr(template, 'autoupdate_factory', None)
        if factory is not None:
            self.__init__(template, opts=opts)
            return factory(self)
        return self

    def __init__(self, template, opts=None):
        """
        Initialization

        :Parameters:
          `template` : `Template`
            Original template instance

          `opts` : any
            Options
        """
        self._original = tpl = template.template()
        self._opts = opts
        super(WrappedTemplate, self).__init__(
            tpl.virgin_tree, tpl.filename, tpl.mtime, tpl.factory, tpl.loader
        )

    def overlay(self, other):
        """
        Overlay this template with another one

        :Parameters:
          `other` : `Template`
            The template layed over self

        :Return: The combined template
        :Rtype: `Template`
        """
        return self.__class__(self._original.overlay(other), opts=self._opts)

    def update_available(self):
        """
        Check for update

        :Return: Update available?
        :Rtype: ``bool``
        """
        return self._original.update_available()

    def reload(self, force=False):
        """
        Reload template(s) if possible and needed

        :Parameters:
          `force` : ``bool``
            Force reload (if possible)?

        :Return: The reloaded (new) template or self
        :Rtype: `Template`
        """
        if force or self.update_available():
            self.__init__(self._original.reload(force=force), self._opts)
        return self
