# -*- coding: ascii -*-
#
# Copyright 2010 - 2012
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
==============
 Deprecations
==============

Deprecations.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

from tdi import util as _util
from tdi.tools import escape as _escape
from tdi.tools import html as _html
from tdi.tools import htmlform as _htmlform
from tdi.tools import javascript as _javascript


_escape.decode_html = _util.Deprecator(_html.decode,
    "tdi.tools.escape.decode_html has been moved to tdi.tools.html.decode."
)
_escape.multiline_to_html = _util.Deprecator(_html.multiline,
    "tdi.tools.escape.multiline_to_html has been moved to "
    "tdi.tools.html.multiline."
)
_escape.escape_js = _util.Deprecator(_javascript.escape_string,
    "tdi.tools.escape.escape_js is deprecated. "
    "Use tdi.tools.javascript.escape_string instead."
)
_htmlform.HTMLForm.multiselect = _util.Deprecator(
    _htmlform.HTMLForm.multiselect,
    "tdi.tools.htmlform.HTMLForm.multiselect is deprecated. Use the 'select' "
    "method with a true 'multiple' attribute instead."
)
