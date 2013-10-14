# -*- coding: ascii -*-
#
# Copyright 2006, 2007, 2008, 2009, 2010
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
==========================
 Modules implemented in C
==========================

The modules in this package implement (or reimplement) various functionality
in C for reasons of performance or availability. The performance
implementations are always re-implementations of accompanying python
functions.

The standard way to import these modules is to use the `load` function. It
catches ImportError and disabled C overrides via environment.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import os as _os

#: Default environment variable name
#:
#: This variable can be set to ``1`` in order to disable loading of tdi's c
#: extensions
#:
#: :Type: ``str``
DEFAULT_ENV_OVERRIDE = 'TDI_NO_C_OVERRIDE'

#: Default template for the fully qualified module name
#:
#: :Type: ``str``
DEFAULT_TPL = 'tdi.c._tdi_%s'


def load(modname, env_override=None, tpl=None):
    """
    Module loading facade

    :Parameters:
      `modname` : ``str``
        Module name part (like ``util`` for ``tdi.c._tdi_util``), see `tpl`

      `env_override` : ``str``
        Name of the environment variable, which can disable the c extension
        import if set to ``1``. If omitted or ``None``,
        `DEFAULT_ENV_OVERRIDE` is applied.

      `tpl` : ``str``
        Template for the fully qualified module name. It has to contain one
        %s format specifier which takes the `modname` part. If omitted or
        ``None``, `DEFAULT_TPL` is applied.

    :Return: The requested module or ``None`` (either by env request or
             ``ImportError``)
    :Rtype: ``module``
    """
    if env_override is None:
        env_override = DEFAULT_ENV_OVERRIDE
    if _os.environ.get(env_override) != '1':
        if tpl is None:
            tpl = DEFAULT_TPL
        try:
            mod = __import__(tpl % modname, globals(), locals(), ['*'])
        except ImportError:
            mod = None
    else:
        mod = None
    return mod
