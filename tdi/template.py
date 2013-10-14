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
==================
 Template Objects
==================

Template Objects.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"
__all__ = ['Template', 'OverlayTemplate', 'AutoUpdate']

import sys as _sys

from tdi._exceptions import Error
from tdi._exceptions import TemplateReloadError
from tdi._exceptions import AutoUpdateWarning
from tdi._exceptions import OverlayError
from tdi import model_adapters as _model_adapters
from tdi import util as _util


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

      `_loader` : ``callable``
        Loader

      `_tree` : ``list``
        The nodetree, the overlay-filtered tree and the prerendered tree
    """
    __slots__ = [
        '__weakref__', 'filename', 'mtime', 'factory', '_loader', '_tree'
    ]

    def tree():
        """
        The node tree with overlay filters

        :Type: `tdi.nodetree.Root`
        """
        # pylint: disable = E0211, W0212, W0612, C0111
        def fget(self):
            return self._prerender(None, None)
        return locals()
    tree = _util.Property(tree)

    def virgin_tree():
        """
        The node tree without overlay filters

        :Type: `tdi.nodetree.Root`
        """
        # pylint: disable = E0211, W0212, W0612, C0111
        def fget(self):
            return self._tree[0]
        return locals()
    virgin_tree = _util.Property(virgin_tree)

    def encoding():
        """
        The template encoding

        :Type: ``str``
        """
        # pylint: disable = E0211, W0612, C0111
        def fget(self):
            return self.tree.encoder.encoding
        return locals()
    encoding = _util.Property(encoding)

    def source_overlay_names():
        """
        Source overlay names

        :Type: iterable
        """
        # pylint: disable = E0211, W0612, C0111
        def fget(self):
            return self.tree.source_overlay_names
        return locals()
    source_overlay_names = _util.Property(source_overlay_names)

    def target_overlay_names():
        """
        Target overlay names

        :Type: iterable
        """
        # pylint: disable = E0211, W0612, C0111
        def fget(self):
            return self.tree.target_overlay_names
        return locals()
    target_overlay_names = _util.Property(target_overlay_names)

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
        self._loader = loader

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

    def reload(self):
        """
        Reload template(s) if possible and needed

        :Return: The reloaded (new) template or self
        :Rtype: `Template`
        """
        if self._loader is not None:
            try:
                tree, mtime = self._loader(self.mtime)
            except (AttributeError, IOError, OSError, Error), e:
                raise TemplateReloadError(str(e))
            if tree is not None:
                return self.__class__(
                    tree, self.filename, mtime, self.factory, self._loader
                )
        return self

    def update_available(self):
        """
        Check for update

        :Return: Update available?
        :Rtype: ``bool``
        """
        if self._loader is not None:
            return self._loader(self.mtime, check_only=True)[0]
        return False

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

        # First: overlay filters
        ftree = otree[1]
        if ftree is None:
            ftree = otree[0]
            if factory.overlay_filters is not None:
                ffactory = factory.replace(**factory.overlay_filters)
                ftree = ffactory.from_string(''.join(list(ftree.render(
                    _model_adapters.RenderAdapter.for_prerender(None,
                        attr=dict(
                            scope=ffactory.builder().analyze.scope,
                            tdi=ffactory.builder().analyze.attribute,
                        )
                    )
                )))).virgin_tree
            otree[1] = ftree

        # Without a model *never* return a prerendered tree
        if model is None:
            return ftree

        # Second: check if prerendering is actually needed.
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

        # Third: actually prerender
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
        tree = factory.from_string(''.join(list(ftree.render(adapted)))).tree

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
    __slots__ = ['_left', '_right']

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

    def reload(self):
        """
        Reload template(s) if possible and needed

        :Return: The reloaded template or self
        :Rtype: `Template`
        """
        if self._left is not None:
            original = self._left.reload()
            overlay = self._right.reload()
            if original is not self._left or overlay is not self._right:
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

    def __init__(self, template):
        """
        Initialization

        :Parameters:
          `template` : `Template`
            The template to autoupdate
        """
        self._template = template.template()

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
        template = self._template
        if template.update_available():
            try:
                self._template = template.reload()
            except TemplateReloadError, e:
                AutoUpdateWarning.emit(
                    'Template autoupdate failed: %s' % str(e)
                )
        return getattr(self._template, name)

    def overlay(self, other):
        """
        Overlay this template with another one

        :Parameters:
          `other` : `Template`
            The template layed over self

        :Return: The combined template
        :Rtype: `Template`
        """
        return self.__class__(OverlayTemplate(self, other, keep=True))
