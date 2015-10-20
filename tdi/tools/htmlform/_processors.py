# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2007 - 2015
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
 HTML form processors
======================

HTML form processors.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"
__all__ = ['TabIndexer']

import itertools as _it

from . import _interfaces


class TabIndexer(object):
    """
    Automatic tabindex filler to be used as `HTMLForm` post processor

    :IVariables:
      `next_index` : ``callable``
        Function to deliver the next index
    """
    __implements__ = [_interfaces.PostProcInterface]

    def __init__(self, start=1):
        """
        Initialization

        :Parameters:
          `start` : ``int``
            Tabindex to start with
        """
        self.next_index = _it.count(start).next

    def __call__(self, method, node, kwargs):
        """
        Add tabindex to form elements

        Exceptions: ``<form>``, ``<option>``, ``<datalist>``,
        ``<input type="hidden">``

        :See: `PostProcInterface`
        """
        if method not in ('form', 'option', 'hidden', 'datalist'):
            node['tabindex'] = self.next_index()
