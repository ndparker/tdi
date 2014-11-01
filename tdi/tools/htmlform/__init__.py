# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2012 - 2014
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

======================
 TDI htmlform package
======================

HTMLForm abstraction.
"""
from __future__ import absolute_import

__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"
_all = []

# pylint: disable = W0401, W0614
from ._adapters import __all__
from ._adapters import *  # noqa
_all.extend(__all__)

from ._interfaces import __all__
from ._interfaces import *  # noqa
_all.extend(__all__)

from ._processors import __all__
from ._processors import *  # noqa
_all.extend(__all__)

from ._main import __all__
from ._main import *  # noqa
_all.extend(__all__)

__all__ = _all
del _all
