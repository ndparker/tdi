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

==============
 Deprecations
==============

Deprecations.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import os as _os
import types as _types

from . import _exceptions
from . import _graph
from . import _util
from . import util as _old_util
from . import _version
from .integration import wtf_service as _wtf_service
from .markup.soup import filters as _filters


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
        # pylint: disable = unidiomatic-typecheck
        if type(todeprecate) is _types.MethodType:
            call = cls(todeprecate.im_func, message=message)

            @_util.decorating(todeprecate.im_func)
            def func(*args, **kwargs):
                """ Wrapper to build a new method """
                # pylint: disable = not-callable
                return call(*args, **kwargs)

            return _types.MethodType(func, None, todeprecate.im_class)
        elif cls == Deprecator and callable(todeprecate):
            res = CallableDeprecator(todeprecate, message=message)
            if type(todeprecate) is _types.FunctionType:
                res = _util.decorating(todeprecate)(res)
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
            # pylint: disable = unidiomatic-typecheck
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
                _exceptions.DeprecationWarning.emit(message, stacklevel=3)
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


if True:
    # pylint: disable = protected-access

    _old_util.CallableDeprecator = Deprecator(
        CallableDeprecator,
        "tdi.util.CallableDeprecator is no longer public. Don't use it."
    )

    _old_util.Deprecator = Deprecator(
        Deprecator,
        "tdi.util.Deprecator is no longer public. Don't use it."
    )

    _old_util.Version = Deprecator(
        _version.Version,
        "tdi.util.Version is no longer public. Don't use it."
    )

    _old_util.DependencyGraph = Deprecator(
        _graph.DependencyGraph,
        "tdi.util.DependencyGraph is no longer public. Don't use it."
    )
    _old_util.DependencyCycle = _graph.DependencyCycle

    _old_util.parse_content_type = Deprecator(
        _filters._parse_content_type,
        "tdi.util.parse_content_type is no longer public. Don't use it."
    )

    _old_util.find_public = Deprecator(
        _util.find_public,
        "tdi.util.find_public is no longer public. Don't use it."
    )

    _old_util.Property = Deprecator(
        _util.Property,
        "tdi.util.Property is no longer public. Don't use it."
    )

    _old_util.decorating = Deprecator(
        _util.decorating,
        "tdi.util.decorating is no longer public. Don't use it."
    )

    _old_util.load_dotted = Deprecator(
        _wtf_service._load_dotted,
        "tdi.util.load_dotted is no longer public. Don't use it."
    )

    def make_dotted(name):
        """
        Generate a dotted module

        :Parameters:
          `name` : ``str``
            Fully qualified module name (like ``tdi.util``)

        :Return: The module object of the last part and the information
                 whether the last part was newly added (``(module, bool)``)
        :Rtype: ``tuple``

        :Exceptions:
         - `ImportError` : The module name was horribly invalid
        """
        import imp as _imp
        import sys as _sys

        sofar, parts = [], name.split('.')
        oldmod = None
        for part in parts:
            if not part:
                raise ImportError("Invalid module name %r" % (name,))
            partname = ".".join(sofar + [part])
            try:
                # pylint: disable = not-callable
                fresh, mod = False, _old_util.load_dotted(partname)
            except ImportError:
                mod = _imp.new_module(partname)
                mod.__path__ = []
                fresh = mod == _sys.modules.setdefault(partname, mod)
            if oldmod is not None:
                setattr(oldmod, part, mod)
            oldmod = mod
            sofar.append(part)

        return mod, fresh

    _old_util.make_dotted = Deprecator(
        make_dotted,
        "tdi.util.make_dotted is no longer public. Don't use it."
    )
