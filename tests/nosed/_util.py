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

import mock as _mock

unset = object()


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
            how = _mock.MagicMock()
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
    # basically stolen from here:
    # http://stackoverflow.com/questions/2481511/mocking-importerror-in-python

    try:
        import builtins
    except ImportError:
        import __builtin__ as builtins
    realimport = builtins.__import__
    realmodules = _sys.modules

    _is_exc = lambda obj: isinstance(obj, BaseException) or (
        isinstance(obj, (type, _types.ClassType))
        and issubclass(obj, BaseException)
    )

    try:
        _sys.modules = dict(realmodules)

        if what in _sys.modules:
            del _sys.modules[what]

        result = _mock.MagicMock() if how is unset else how

        def myimport(name, globals={}, locals={}, fromlist=[], level=-1):
            """ Fake importer """
            # pylint: disable = redefined-builtin, dangerous-default-value

            if name == what:
                if _is_exc(result):
                    raise result
                return result
            else:
                kwargs = dict(
                    globals=globals,
                    locals=locals,
                    fromlist=fromlist,
                )
                if level != -1:
                    kwargs['level'] = level
                return realimport(name, **kwargs)

        builtins.__import__ = myimport
        try:
            yield result
        finally:
            builtins.__import__ = realimport
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
