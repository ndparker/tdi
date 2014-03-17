# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2013 - 2014
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
 Template Tools
================

Template Tools.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import pprint as _pprint

from tdi import _exceptions
from tdi import util as _util


class TemplateUndecided(_exceptions.DependencyError):
    """
    Template could not be determined, because the decision is ambiguous

    The exception argument is a dict mapping undecidable overlay names to
    the respective set of template names
    """


class TemplateListProxy(object):
    """
    Proxy `TemplateList` instances for lazy creation

    :IVariables:
      `_list` : ``callable``
        List creator

      `__list` : ``list``
        List cache (if possible)
    """

    def __init__(self, creator, autoreload):
        """
        Initialization

        :Parameters:
          `creator` : ``callable``
            List creator function

          `autoreload` : ``bool``
            Autoreload possible?
        """
        if autoreload:
            create = creator
        else:
            self.__list = None
            def create():
                """ self-destroying creator """
                if self.__list is None:
                    self.__list = creator()
                    self._list = lambda: self.__list
                return self.__list
        self._list = create

    def __getattr__(self, name):
        return getattr(self._list(), name)

    def __len__(self):
        return len(self._list())

    def __repr__(self):
        return repr(self._list())

    def __str__(self):
        return str(self._list())

    def __add__(self, other):
        return self._list() + other

    def __mul__(self, other):
        return self._list() * other

    def __getitem__(self, index):
        return self._list()[index]

    def __contains__(self, item):
        return item in self._list()

    def __hash__(self):
        return hash(self._list())

    def __cmp__(self, other):
        return cmp(self._list(), other)

    def __iter__(self):
        return iter(self._list())


class TemplateList(list):
    """
    Container for template names

    This class contains the resulting template list, generated by the
    layout code.

    :IVariables:
      `missing` : ``list`` or ``None``
        Missing overlays
    """
    missing = None

    def __init__(*args, **kwargs): # pylint: disable = E0211
        """
        Initialization

        :Keywords:
          `MISSING` : ``iterable``
            Missing overlay list
        """
        self, args = args[0], args[1:]
        missing = kwargs.pop('MISSING', None)
        if kwargs:
            raise TypeError("Unrecognized keywords")
        super(TemplateList, self).__init__(*args)
        self.missing = list(missing or ()) or None

    def __repr__(self):
        """
        Debug representation

        :Return: The debug string
        :Rtype: ``str``
        """
        return "%s(%s%s,%sMISSING=%s%s)" % (
            self.__class__.__name__,
            self and '\n' or '',
            _pprint.pformat(list(self)),
            self and '\n\n ' or ' ',
            self.missing and '\n' or ' ',
            _pprint.pformat(self.missing)
        )


class Layout(object):
    """
    Create template lists based on a start configuration

    :IVariables:
      `_base` : ``tuple``
        Base template list

      `_use` : ``dict``
        extra overlay -> filename mapping

      `_ignore` : ``frozenset``
        Template names to ignore
    """

    def __init__(self, loader, *base, **kwargs):
        """
        Initialization

        :Parameters:
          `loader` : `Loader`
            Template loader

          `base` : ``tuple``
            Base template list

          `kwargs` : ``dict``
            Keywords

        :Keywords:
          `use` : ``dict``
            extra overlay -> filename mapping

          `ignore` : ``iterable``
            template names to ignore

          `cls` : ``callable``
            template list factory. If omitted or ``None``, `TemplateList` is
            used.

          `lazy` : ``bool``
            Lazy loading?
        """
        use = kwargs.pop('use', None)
        ignore = kwargs.pop('ignore', None)
        cls = kwargs.pop('cls', None)
        lazy = kwargs.pop('lazy', None)
        if kwargs:
            raise TypeError("Unrecognized keywords")
        self._base = base
        self._use = dict(use or ())
        self._ignore = frozenset(ignore or ())
        self._loader = loader
        self._cls = cls is None and TemplateList or cls
        self._lazy = lazy is None and True or bool(lazy)

    def extend(self, *base, **kwargs):
        """
        Extend the layout and create a new one.

        :Parameters:
          `base` : ``tuple``
            Base template list

          `kwargs` : ``dict``
            Keywords

        :Keywords:
          `use` : ``dict``
            extra overlay -> filename mapping

          `ignore` : ``iterable``
            template names to ignore

          `consider` : ``iterable``
            Template names to "unignore"

        :Return: New layout
        :Rtype: `Layout`
        """
        use = kwargs.pop('use', None)
        ignore = kwargs.pop('ignore', None)
        consider = kwargs.pop('consider', None)
        if kwargs:
            raise TypeError("Unrecognized keywords")
        newbase = tuple(self._base) + base
        newuse = self._use
        if use:
            newuse = dict(newuse)
            newuse.update(use)
        newignore = self._ignore
        if ignore or consider:
            newignore = set(newignore)
            if ignore:
                newignore.update(set(ignore))
            if consider:
                newignore -= set(consider)
        return self.__class__(self._loader, *newbase, **dict(
            use=newuse, ignore=newignore, cls=self._cls, lazy=self._lazy
        ))

    def _make_creator(self, base, use, ignore):
        """ Make a new template list creator """
        cls, loader = self._cls, self._loader
        def creator():
            """ Create """
            result, missing, undecided = discover(
                loader, base, use=use, ignore=ignore
            )
            if undecided:
                raise TemplateUndecided(undecided)
            return cls(result, MISSING=missing)
        return creator

    def __call__(self, *names, **kwargs):
        """
        Create a template list from this layout

        :Parameters:
          `names` : ``tuple``
            Base template list

          `kwargs` : ``dict``
            Keywords

        :Keywords:
          `use` : ``dict``
            extra overlay -> filename mapping

          `ignore` : ``iterable``
            template names to ignore

          `consider` : ``iterable``
            Template names to "unignore"

        :Return: template list
        :Rtype: `TemplateList`
        """
        use_ = kwargs.pop('use', None)
        ignore_ = kwargs.pop('ignore', None)
        consider = kwargs.pop('consider', None)
        if kwargs:
            raise TypeError("Unrecognized keywords")
        base = tuple(self._base) + names
        use = dict(self._use)
        if use_:
            use.update(use_)
        ignore = set(self._ignore)
        if ignore_:
            ignore.update(set(ignore_))
        if consider:
            ignore -= set(consider)

        lazy, autoreload = self._lazy, self._loader.autoreload()
        creator = self._make_creator(base, use, ignore)
        if not lazy and not autoreload:
            return creator()
        result = TemplateListProxy(creator, autoreload)
        if not lazy:
            iter(result) # trigger list creation
        return result


def distinct_overlays(tpl):
    """
    Extract distinct overlay names of a template

    Overlay names available both as target and source within the template
    are discarded.

    :Parameters:
      `tpl` : `tdi.template.Template`
        Template to inspect

    :Return: set(targets), set(sources)
    :Rtype: ``tuple``
    """
    targets = set(tpl.target_overlay_names)
    sources = set(tpl.source_overlay_names)
    return targets - sources, sources - targets


def discover(loader, names, use=None, ignore=None):
    """
    Find templates to use and order them topologically correct

    :Parameters:
      `loader` : `Loader`
        Template loader

      `names` : ``iterable``
        Base names. These templates are always added first, in order and
        define the initial list of overlays to discover.

      `use` : ``dict``
        Extra target mapping (overlay name -> template name). This is
        used, before the global overlay mapping is asked. Pass ambiguous
        overlay decisions here, or disable certain overlays by passing
        ``None`` as name.

      `ignore` : ``iterable``
        List of template names to ignore completely.

    :Return: list(template names), set(missing overlays),
             dict(undecidable overlays -> possible template names)
    :Rtype: ``tuple``
    """
    # pylint: disable = R0912

    names, missing, undecided = list(names), set(), {}
    if not names:
        return names, missing, undecided

    overlays = lambda x: distinct_overlays(loader.load(x))
    available = loader.available()

    names.reverse()
    dep = names.pop()
    use, ignore = dict(use or ()), set(ignore or ())
    targets, graph = set(overlays(dep)[0]), _util.DependencyGraph()

    # initial templates
    while names:
        tname = names.pop()
        ttargets, tsources = overlays(tname)
        targets -= tsources
        targets |= ttargets
        graph.add(dep, tname)
        dep = tname

    # automatic templates
    targets = dict((target, set([dep])) for target in targets)
    while targets:
        target, deps = targets.popitem()
        ttargets = None

        if target in use:
            tname = use[target]
            if tname is None:
                missing.add(target)
                continue
            else:
                ttargets, tsources = overlays(tname)
                if target not in tsources:
                    raise AssertionError('"use" source %r not in %r' % (
                        target, tname
                    ))
        else:
            tnames = [
                tname
                for tname in available.get(target) or ()
                if tname not in ignore
            ]
            if not tnames:
                missing.add(target)
                continue
            elif len(tnames) > 1:
                undecided[target] = tuple(sorted(tnames))
                continue
            tname = tnames[0]

        if ttargets is None:
            ttargets = overlays(tname)[0]
        for dep in deps:
            graph.add(dep, tname)
        for target in ttargets:
            if target not in targets:
                targets[target] = set()
            targets[target].add(tname)

    return graph.resolve(), missing, undecided


class Loader(object):
    """
    Find, load and select templates

    :IVariables:
      `_available` : ``dict`` or ``None``
        The mapping cache. This dict contains the overlay -> template mapping.
        If ``None``, the dict is created during the next call of the
        ``available`` method.

      `_registered` : ``set``
        List of template names registered for autoreload

      `_load` : callable
        Loader

      `_list` : callable
        Lister

      `_select` : callable
        Selector
    """

    def __init__(self, list, load, select): # pylint: disable = W0622
        """
        Initialization

        :Parameters:
          `list` : callable
            Template lister. This function is called without parameters and
            expected to return a list of all template names available.
            Template names are hashable tokens (such as strings) identifying
            the templates. They are passed to the `load` function if the
            template needs to be loaded.

          `load` : callable
            Template loader. This function is called with a template name as
            parameter and expected to return the actual template object.

          `select` : callable
            Template selector. This function is called with two parameters:
            The loader instance (self) and the template name. It is expected
            to return a bool value, which decides whether this template is
            in the pool for automatic templates or not.
        """
        self._available = None
        self._registered = set()
        self._load = load
        self._list = list
        self._select = select

    def autoreload(self):
        """
        Autoreload templates?

        :Return: Autoreloading available?
        :Rtype: ``bool``
        """
        return bool(self._registered)

    def _callback(self, _):
        """ Autoupdate callback - reset the source mapping """
        self._available = None

    def load(self, name):
        """
        Load a single template and register the autoupdate callback

        :Parameters:
          `name` : hashable
            Template name

        :Return: The template
        :Rtype: `tdi.template.Template`
        """
        tpl = self._load(name)
        if name not in self._registered:
            register = getattr(tpl, 'autoupdate_register_callback', None)
            if register is not None:
                register(self._callback)
                self._registered.add(name)
        return tpl

    def available(self):
        """
        Determine automatic overlay -> template name mapping

        This method should only list the automatic overlay mappings.

        :Return: source overlay name -> set(template name)
        :Rtype: ``dict``
        """
        result = self._available
        if result is None:
            result = {}
            for name in self._list():
                if self._select(self, name):
                    tpl = self.load(name)
                    for source in distinct_overlays(tpl)[1]:
                        if source not in result:
                            result[source] = set()
                        result[source].add(name)
            self._available = result
        return result
