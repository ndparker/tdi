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
================
 Misc Utilities
================

Misc utilities.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import imp as _imp
import inspect as _inspect
import os as _os
import re as _re
import sys as _sys
import types as _types
import warnings as _warnings

from tdi import _exceptions


def _make_parse_content_type():
    """
    Make content type parser

    :Return: parse_content_type
    :Rtype: ``callable``
    """
    # These are a bit more lenient than RFC 2045.
    tokenres = r'[^\000-\040()<>@,;:\\"/[\]?=]+'
    qcontent = r'[^\000\\"]'
    qsres = r'"%(qc)s*(?:\\"%(qc)s*)*"' % {'qc': qcontent}
    valueres = r'(?:%(token)s|%(quoted-string)s)' % {
        'token': tokenres, 'quoted-string': qsres,
    }

    typere = _re.compile(
        r'\s*([^;/\s]+/[^;/\s]+)((?:\s*;\s*%(key)s\s*=\s*%(val)s)*)\s*$' %
        {'key': tokenres, 'val': valueres,}
    )
    pairre = _re.compile(r'\s*;\s*(%(key)s)\s*=\s*(%(val)s)' % {
        'key': tokenres, 'val': valueres
    })
    stripre = _re.compile(r'\r?\n')

    def parse_content_type(value): # pylint: disable = W0621
        """
        Parse a content type

        :Warning: comments are not recognized (yet?)

        :Parameters:
          `value` : ``basestring``
            The value to parse - must be ascii compatible

        :Return: The parsed header (``(value, {key, [value, value, ...]})``)
                 or ``None``
        :Rtype: ``tuple``
        """
        try:
            if isinstance(value, unicode):
                value.encode('ascii')
            else:
                value.decode('ascii')
        except (AttributeError, UnicodeError):
            return None

        match = typere.match(value)
        if not match:
            return None

        parsed = (match.group(1).lower(), {})
        match = match.group(2)
        if match:
            for key, val in pairre.findall(match):
                if val[:1] == '"':
                    val = stripre.sub(r'', val[1:-1]).replace(r'\"', '"')
                parsed[1].setdefault(key.lower(), []).append(val)

        return parsed

    return parse_content_type

parse_content_type = _make_parse_content_type()


class Version(tuple):
    """
    Represents the package version

    :IVariables:
      `major` : ``int``
        The major version number

      `minor` : ``int``
        The minor version number

      `patch` : ``int``
        The patch level version number

      `is_dev` : ``bool``
        Is it a development version?

      `revision` : ``int``
        SVN Revision
    """

    def __new__(cls, versionstring, is_dev, revision):
        """
        Construction

        :Parameters:
          `versionstring` : ``str``
            The numbered version string (like ``"1.1.0"``)
            It should contain at least three dot separated numbers

          `is_dev` : ``bool``
            Is it a development version?

          `revision` : ``int``
            SVN Revision

        :Return: New version instance
        :Rtype: `version`
        """
        # pylint: disable = W0613
        tup = []
        versionstring = versionstring.strip()
        if versionstring:
            for item in versionstring.split('.'):
                try:
                    item = int(item)
                except ValueError:
                    pass
                tup.append(item)
        while len(tup) < 3:
            tup.append(0)
        return tuple.__new__(cls, tup)

    def __init__(self, versionstring, is_dev, revision):
        """
        Initialization

        :Parameters:
          `versionstring` : ``str``
            The numbered version string (like ``1.1.0``)
            It should contain at least three dot separated numbers

          `is_dev` : ``bool``
            Is it a development version?

          `revision` : ``int``
            SVN Revision
        """
        # pylint: disable = W0613
        super(Version, self).__init__()
        self.major, self.minor, self.patch = self[:3]
        self.is_dev = bool(is_dev)
        self.revision = int(revision)

    def __repr__(self):
        """
        Create a development string representation

        :Return: The string representation
        :Rtype: ``str``
        """
        return "%s.%s(%r, is_dev=%r, revision=%r)" % (
            self.__class__.__module__,
            self.__class__.__name__,
            ".".join(map(str, self)),
            self.is_dev,
            self.revision,
        )

    def __str__(self):
        """
        Create a version like string representation

        :Return: The string representation
        :Rtype: ``str``
        """
        return "%s%s" % (
            ".".join(map(str, self)),
            ("", "-dev-r%d" % self.revision)[self.is_dev],
        )

    def __unicode__(self):
        """
        Create a version like unicode representation

        :Return: The unicode representation
        :Rtype: ``unicode``
        """
        return str(self).decode('ascii')


def find_public(space):
    """
    Determine all public names in space

    :Parameters:
      `space` : ``dict``
        Name space to inspect

    :Return: List of public names
    :Rtype: ``list``
    """
    if space.has_key('__all__'):
        return list(space['__all__'])
    return [key for key in space.keys() if not key.startswith('_')]


def Property(func): # pylint: disable = C0103
    """
    Property with improved docs handling

    :Parameters:
      `func` : ``callable``
        The function providing the property parameters. It takes no arguments
        as returns a dict containing the keyword arguments to be defined for
        ``property``. The documentation is taken out the function by default,
        but can be overridden in the returned dict.

    :Return: The requested property
    :Rtype: ``property``
    """
    kwargs = func()
    kwargs.setdefault('doc', func.__doc__)
    kwargs = kwargs.get
    return property(
        fget=kwargs('fget'),
        fset=kwargs('fset'),
        fdel=kwargs('fdel'),
        doc=kwargs('doc'),
    )


def decorating(decorated, extra=None):
    """
    Create decorator for designating decorators.

    :Parameters:
      `decorated` : function
        Function to decorate

      `extra` : ``dict``
        Dict of consumed keyword parameters (not existing in the originally
        decorated function), mapping to their defaults. If omitted or
        ``None``, no extra keyword parameters are consumed. The arguments
        must be consumed by the actual decorator function.

    :Return: Decorator
    :Rtype: ``callable``
    """
    # pylint: disable = R0912
    def flat_names(args):
        """ Create flat list of argument names """
        for arg in args:
            if isinstance(arg, basestring):
                yield arg
            else:
                for arg in flat_names(arg):
                    yield arg
    name = decorated.__name__
    try:
        dargspec = argspec = _inspect.getargspec(decorated)
    except TypeError:
        dargspec = argspec = ([], 'args', 'kwargs', None)
    if extra:
        keys = extra.keys()
        argspec[0].extend(keys)
        defaults = list(argspec[3] or ())
        for key in keys:
            defaults.append(extra[key])
        argspec = (argspec[0], argspec[1], argspec[2], defaults)

    # assign a name for the proxy function.
    # Make sure it's not already used for something else (function
    # name or argument)
    counter, proxy_name = -1, 'proxy'
    names = dict.fromkeys(flat_names(argspec[0]))
    names[name] = None
    while proxy_name in names:
        counter += 1
        proxy_name = 'proxy%s' % counter

    def inner(decorator):
        """ Actual decorator """
        # Compile wrapper function
        space = {proxy_name: decorator}
        if argspec[3]:
            kwnames = argspec[0][-len(argspec[3]):]
        else:
            kwnames = None
        passed = _inspect.formatargspec(argspec[0], argspec[1], argspec[2],
            kwnames, formatvalue=lambda value: '=' + value
        )
        # pylint: disable = W0122
        exec "def %s%s: return %s%s" % (
            name, _inspect.formatargspec(*argspec), proxy_name, passed
        ) in space
        wrapper = space[name]
        wrapper.__dict__ = decorated.__dict__
        wrapper.__doc__ = decorated.__doc__
        if extra and decorated.__doc__ is not None:
            if not decorated.__doc__.startswith('%s(' % name):
                wrapper.__doc__ = "%s%s\n\n%s" % (
                    name,
                    _inspect.formatargspec(*dargspec),
                    decorated.__doc__,
                )
        return wrapper

    return inner


class Deprecator(object):
    """
    Deprecation proxy class

    The class basically emits a deprecation warning on access.

    :IVariables:
      `__todeprecate` : any
        Object to deprecate

      `__warn` : ``callable``
        Warn function
    """
    def __new__(cls, todeprecate, message=None):
        """
        Construct

        :Parameters:
          `todeprecate` : any
            Object to deprecate

          `message` : ``str``
            Custom message. If omitted or ``None``, a default message is
            generated.

        :Return: Deprecator instance
        :Rtype: `Deprecator`
        """
        # pylint: disable = W0613
        if type(todeprecate) is _types.MethodType:
            call = cls(todeprecate.im_func, message=message)
            @decorating(todeprecate.im_func)
            def func(*args, **kwargs):
                """ Wrapper to build a new method """
                return call(*args, **kwargs) # pylint: disable = E1102
            return _types.MethodType(func, None, todeprecate.im_class)
        elif cls == Deprecator and callable(todeprecate):
            res = CallableDeprecator(todeprecate, message=message)
            if type(todeprecate) is _types.FunctionType:
                res = decorating(todeprecate)(res)
            return res
        return object.__new__(cls)

    def __init__(self, todeprecate, message=None):
        """
        Initialization

        :Parameters:
          `todeprecate` : any
            Object to deprecate

          `message` : ``str``
            Custom message. If omitted or ``None``, a default message is
            generated.
        """
        self.__todeprecate = todeprecate
        if message is None:
            if type(todeprecate) is _types.FunctionType:
                name = todeprecate.__name__
            else:
                name = todeprecate.__class__.__name__
            message = "%s.%s is deprecated." % (todeprecate.__module__, name)
        if _os.environ.get('EPYDOC_INSPECTOR') == '1':
            def warn():
                """ Dummy to not clutter epydoc output """
                pass
        else:
            def warn():
                """ Emit the message """
                _warnings.warn(message,
                    category=_exceptions.DeprecationWarning, stacklevel=3
                )
        self.__warn = warn

    def __getattr__(self, name):
        """ Get attribute with deprecation warning """
        self.__warn()
        return getattr(self.__todeprecate, name)

    def __iter__(self):
        """ Get iterator with deprecation warning """
        self.__warn()
        return iter(self.__todeprecate)


class CallableDeprecator(Deprecator):
    """ Callable proxy deprecation class """

    def __call__(self, *args, **kwargs):
        """ Call with deprecation warning """
        self._Deprecator__warn()
        return self._Deprecator__todeprecate(*args, **kwargs)


def load_dotted(name):
    """
    Load a dotted name

    The dotted name can be anything, which is passively resolvable
    (i.e. without the invocation of a class to get their attributes or
    the like). For example, `name` could be 'tdi.util.load_dotted'
    and would return this very function. It's assumed that the first
    part of the `name` is always is a module.

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


def make_dotted(name):
    """
    Generate a dotted module

    :Parameters:
      `name` : ``str``
        Fully qualified module name (like ``tdi.util``)

    :Return: The module object of the last part and the information whether
             the last part was newly added (``(module, bool)``)
    :Rtype: ``tuple``

    :Exceptions:
     - `ImportError` : The module name was horribly invalid
    """
    sofar, parts = [], name.split('.')
    oldmod = None
    for part in parts:
        if not part:
            raise ImportError("Invalid module name %r" % (name,))
        partname = ".".join(sofar + [part])
        try:
            fresh, mod = False, load_dotted(partname)
        except ImportError:
            mod = _imp.new_module(partname)
            mod.__path__ = []
            fresh = mod == _sys.modules.setdefault(partname, mod)
        if oldmod is not None:
            setattr(oldmod, part, mod)
        oldmod = mod
        sofar.append(part)

    return mod, fresh
