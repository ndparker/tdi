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

================
 Misc Utilities
================

Misc utilities.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import inspect as _inspect


def find_public(space):
    """
    Determine all public names in space

    :Parameters:
      `space` : ``dict``
        Name space to inspect

    :Return: List of public names
    :Rtype: ``list``
    """
    if '__all__' in space:
        return list(space['__all__'])
    return [key for key in space.keys() if not key.startswith('_')]


def Property(func):
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
    # pylint: disable = invalid-name

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
        passed = _inspect.formatargspec(
            argspec[0], argspec[1], argspec[2], kwnames,
            formatvalue=lambda value: '=' + value
        )
        exec "def %s%s: return %s%s" % (  # pylint: disable = exec-used
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
