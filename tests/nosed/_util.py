# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2014 - 2015
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
 Test Utilities
================

Test utilities.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import contextlib as _contextlib
import functools as _ft
import sys as _sys
import types as _types

import mock
from nose import SkipTest

unset = type('unset', (object,), {})()


@_contextlib.contextmanager
def patched(where, what, how=unset):
    """
    Context manager to replace a symbol with a mock temporarily

    :Parameters:
      `where` : any
        Namespace, where `what` resides

      `what` : ``str``
        Name of the symbol, which should be replaced

      `how` : any
        How should it be replaced? If omitted or `unset`, a new MagicMock
        instance is created. The result is yielded as context.
    """
    try:
        old = getattr(where, what)
    except AttributeError:
        pass
    try:
        if how is unset:
            how = mock.MagicMock()
        setattr(where, what, how)
        yield how
    finally:
        try:
            old
        except NameError:
            delattr(where, what)
        else:
            setattr(where, what, old)


def patch(where, what, how=unset, name=None):
    """
    Decorator replacing attributes temporarily with mocks

    :Parameters:
      `where` : any
        Namespace, where `what` resides

      `what` : ``str``
        Name of the symbol, which should be replaced

      `how` : any
        How should it be replaced? If omitted or `unset`, a new MagicMock
        instance is created.

      `name` : ``str``
        The keyword argument name, which should be used to pass the fake
        object to the decorated function. If omitted or ``None``, the fake
        object won't be passed.

    :Return: Decorator function
    :Rtype: callable
    """
    def inner(func):
        """
        Actual decorator

        :Parameters:
          `func` : callable
            Function to decorate

        :Return: Proxy function wrapping `func`
        :Rtype: callable
        """
        @_ft.wraps(func)
        def proxy(*args, **kwargs):
            """ Function proxy """
            with patched(where, what, how) as fake:
                if name is not None:
                    kwargs[name] = fake
                return func(*args, **kwargs)
        return proxy
    return inner


@_contextlib.contextmanager
def patched_import(what, how=unset):
    """
    Context manager to mock an import statement temporarily

    :Parameters:
      `what` : ``str``
        Name of the module to mock

      `how` : any
        How should it be replaced? If omitted or `unset`, a new MagicMock
        instance is created. The result is yielded as context.
    """
    # basically stolen from svnmailer

    _is_exc = lambda obj: isinstance(obj, BaseException) or (
        isinstance(obj, (type, _types.ClassType))
        and issubclass(obj, BaseException)
    )

    class FinderLoader(object):
        """ Finder / Loader for meta path """

        def __init__(self, fullname, module):
            self.module = module
            self.name = fullname
            extra = '%s.' % fullname
            for key in _sys.modules.keys():
                if key.startswith(extra):
                    del _sys.modules[key]
            if fullname in _sys.modules:
                del _sys.modules[fullname]

        def find_module(self, fullname, path=None):
            """ Find the module """
            # pylint: disable = unused-argument
            if fullname == self.name:
                return self
            return None

        def load_module(self, fullname):
            """ Load the module """
            if _is_exc(self.module):
                raise self.module
            _sys.modules[fullname] = self.module
            return self.module

    realmodules = _sys.modules
    try:
        _sys.modules = dict(realmodules)
        obj = FinderLoader(what, mock.MagicMock() if how is unset else how)
        realpath = _sys.meta_path
        try:
            _sys.meta_path = [obj] + _sys.meta_path
            old, parts = unset, what.rsplit('.', 1)
            if len(parts) == 2:
                parent, base = parts[0], parts[1]
                if parent in _sys.modules:
                    parent = _sys.modules[parent]
                    if hasattr(parent, base):
                        old = getattr(parent, base)
                        setattr(parent, base, obj.module)
            try:
                yield obj.module
            finally:
                if old is not unset:
                    setattr(parent, base, old)
        finally:
            _sys.meta_path = realpath
    finally:
        _sys.modules = realmodules


def patch_import(what, how=unset, name=None):
    """
    Decorator to mock an import statement temporarily

    :Parameters:
      `what` : ``str``
        Name of the module to mock

      `how` : any
        How should it be replaced? If omitted or `unset`, a new MagicMock
        instance is created.

      `name` : ``str``
        The keyword argument name, which should be used to pass the fake
        object to the decorated function. If omitted or ``None``, the fake
        object won't be passed.

    :Return: Decorator function
    :Rtype: callable
    """
    def inner(func):
        """
        Actual decorator

        :Parameters:
          `func` : callable
            Function to decorate

        :Return: Proxy function wrapping `func`
        :Rtype: callable
        """
        @_ft.wraps(func)
        def proxy(*args, **kwargs):
            """ Function proxy """
            with patched_import(what, how=how) as fake:
                if name is not None:
                    kwargs[name] = fake
                return func(*args, **kwargs)
        return proxy
    return inner


class Bunch(object):
    """ Bunch object - represent all init kwargs as attributes """

    def __init__(self, **kw):
        """ Initialization """
        self.__dict__.update(kw)


def python_impl(*module):
    """
    Decorator to ensure python implementation usage in module(s)

    :Parameters:
      `module` : ``tuple``
        Modules to set up (at least one)

    :Return: Decorator function
    :Rtype: callable
    """
    assert module

    def inner(func):
        """ Actual decorator """
        @_ft.wraps(func)
        def proxy(*args, **kwargs):
            """ Proxy function, mocking c loader and stuff """
            try:
                with patched_import('tdi.c') as c:
                    c.load.side_effect = lambda *x: None
                    for mod in module:
                        reload(mod)
                    return func(*args, **kwargs)
            finally:
                for mod in module:
                    reload(mod)
        return proxy
    return inner


def c_impl(*module, **kwargs):
    """
    c_impl(*module, test=None)

    Decorator to ensure c implementation usage in module(s)

    if c loader doesn't load, the test will be skipped.

    :Parameters:
      `module` : ``tuple``
        Modules to set up (at least one)

      `test` : ``str``
        Module name (part) to pass to the loader in order to test it. If
        omitted or ``None``, 'impl' is used.

    :Return: Decorator
    :Rtype: callable
    """
    assert module
    test = kwargs.pop('test', None)
    if kwargs:
        raise TypeError("Unrecognized arguments")
    if test is None:
        test = 'impl'

    def inner(func):
        """ Actual decorator """
        @_ft.wraps(func)
        def proxy(*args, **kwargs):
            """ Proxy function """
            from tdi import c
            if c.load(test) is None:
                raise SkipTest("c extension not found")
            for mod in module:
                reload(mod)
            return func(*args, **kwargs)
        return proxy
    return inner


def multi_impl(space, *module, **kwargs):
    """
    multi_impl(space, *module, test=None, name=None)

    Decorator to create test functions for all implementations

    :Parameters:
      `space` : ``dict``
        Namespace to create these functions in

      `module` : ``tuple``
        Modules to set up (at least one)

      `test` : ``str``
        Module name (part) to test - passed to c_impl. If omitted or ``None``,
        a default is picked (by c_impl)

      `name` : ``str``
        test function argument name to pass the current implementation name
        ('py' or 'c'). If omitted or ``None``, the info is not passed.

    :Return: Decorator function
    :Rtype: callable
    """
    assert module

    test = kwargs.pop('test', None)
    arg = kwargs.pop('name', None)
    if kwargs:
        raise TypeError("Unrecognized arguments")

    if arg is None:
        arger = lambda x, y: y
    else:
        def arger(impl, func):
            """ Decorator function to inject impl as arg """
            @_ft.wraps(func)
            def proxy(*args, **kwargs):
                """ Proxy function """
                kwargs[arg] = impl
                return func(*args, **kwargs)
            return proxy

    def inner(func):
        """ Actual decorator """
        name = func.__name__
        if name.startswith('test'):
            name = name[4:]
        while name.startswith('_'):
            name = name[1:]

        space['test_py__' + name] = pfunc = arger(
            'py', python_impl(*module)(func)
        )
        space['test_c__' + name] = cfunc = arger(
            'c', c_impl(*module, **{'test': test})(func)
        )
        func.__test__ = False
        if pfunc.__doc__:
            pfunc.__doc__ = '[py] %s' % pfunc.__doc__.lstrip()
        if cfunc.__doc__:
            cfunc.__doc__ = '[c] %s' % cfunc.__doc__.lstrip()
        return func
    return inner


def uni(value):
    """
    Create unicode from raw string with unicode escapes

    :Parameters:
      `value` : ``str``
        String, which encodes to ascii and decodes as unicode_escape

    :Return: The decoded string
    :Rtype: ``unicode``
    """
    return value.encode('ascii').decode('unicode_escape')
