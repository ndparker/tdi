# -*- coding: ascii -*-
#
# Copyright 2006 - 2012
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
===============================
 Template Data Interface (TDI)
===============================

Template Data Interface (TDI).
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"
__license__ = "Apache License, Version 2.0"
__version__ = ('0.9.9.7', False, 4807)

from tdi import util as _util
from tdi._exceptions import * # pylint: disable = W0401, W0614, W0622
from tdi.markup import factory as _factory

#: Version of the TDI package
#:
#: :Type: `tdi.util.Version`
version = _util.Version(*__version__)

#: HTML Template factory
#:
#: :Type: `tdi.factory.Factory`
html = _factory.html

#: XML Template factory
#:
#: :Type: `tdi.factory.Factory`
xml = _factory.xml

#: Text Template factory
#:
#: :Type: `tdi.factory.Factory`
text = _factory.text

__all__ = _util.find_public(globals())
del _util, _factory

from tdi import _deprecations # pylint: disable = W0611
