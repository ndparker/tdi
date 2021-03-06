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

===============================
 Template Data Interface (TDI)
===============================

Template Data Interface (TDI).
"""
if __doc__:  # pragma: no cover
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"
__license__ = "Apache License, Version 2.0"
__version__ = ('0.9.9.9', False, 4810)

from tdi import _util
from tdi import _version
if 1:
    # pylint: disable = redefined-builtin
    # pylint: disable = wildcard-import
    from tdi._exceptions import *  # noqa
del reraise  # noqa
from .markup import factory as _factory

#: Version of the TDI package
#:
#: :Type: `tdi.util.Version`
version = _version.Version(*__version__)

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
del _factory

from tdi import _deprecations  # noqa
