# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2014
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
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import contextlib as _contextlib
import functools as _functools

import mock as _mock

unset = object()


@_contextlib.contextmanager
def mocked(where, what, how=unset):
    """
    Context manager which replaces a symbol temporarily

    :Parameters:
      `where` : any
        Namespace, where `what` resides

      `what` : ``str``
        Name of the symbol, which should be replaced

      `how` : any
        How should it be replaced? If omitted or `unset`, a new MagicMock
        instance is created. The result is yielded as context.
    """
    old = getattr(where, what)
    try:
        if how is unset:
            how = _mock.MagicMock()
        setattr(where, what, how)
        yield how
    finally:
        setattr(where, what, old)


def mock(where, what, how=unset, name=None):
    """
    Decorator-Configurator for pre-creating mocks

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
        @_functools.wraps(func)
        def proxy(*args, **kwargs):
            """ Function proxy """
            with mocked(where, what, how=how) as fake:
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
