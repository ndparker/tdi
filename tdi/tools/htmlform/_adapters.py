# -*- coding: ascii -*-
#
# Copyright 2007 - 2012
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
=====================
 HTML forms reloaded
=====================

Form helper classes.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"
__all__ = [
    'DictParameterAdapter', 'ListDictParameterAdapter',
    'MultiDictParameterAdapter', 'NullParameterAdapter',
]

from tdi.tools.htmlform._interfaces import ParameterAdapterInterface


class DictParameterAdapter(object):
    """
    HTMLForm parameter adapter from a simple dict

    :IVariables:
      `param` : ``dict``
        Parameters
    """
    __implements__ = [ParameterAdapterInterface]

    def __init__(self, param):
        """
        Initialization

        :Parameters:
          `param` : ``dict``
            Parameters
        """
        self.param = param

    def getfirst(self, name, default=None):
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        return self.param.get(name, default)

    def getlist(self, name): # pylint: disable = E0202
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        if name in self.param:
            return [self.param[name]]
        return []


class ListDictParameterAdapter(object):
    """
    HTMLForm parameter adapter from a dict of sequences

    :IVariables:
      `param` : dict of sequences
        Parameters
    """
    __implements__ = [ParameterAdapterInterface]

    def __init__(self, param):
        """
        Initialization

        :Parameters:
          `param` : dict of sequences
            Parameters. Empty sequences act as if the key was not present.
            Otherwise ``getfirst`` will return the first element and
            ``getlist`` will return a shallow copy of the sequence as a
            ``list``.
        """
        self.param = param

    def getfirst(self, name, default=None):
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        try:
            result = self.param[name]
        except KeyError:
            pass
        else:
            if result:
                return result[0]
        return default

    def getlist(self, name):
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        try:
            result = self.param[name]
        except KeyError:
            pass
        else:
            return list(result)
        return []


class MultiDictParameterAdapter(object):
    """
    HTMLForm parameter adapter from a multidict (like paste provides)

    :IVariables:
      `param` : multidict
        Parameters
    """
    __implements__ = [ParameterAdapterInterface]

    def __init__(self, param):
        """
        Initialization

        :Parameters:
          `param` : multidict
            Parameters. The object is expected to provide a getall() method
        """
        self.param = param

    def getfirst(self, name, default=None):
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        try:
            return self.param.getall(name)[0]
        except IndexError:
            return default

    def getlist(self, name): # pylint: disable = E0202
        """ :See: ``tdi.tools.htmlform.ParameterAdapterInterface`` """
        return self.param.getall(name)


class NullParameterAdapter(object):
    """ This adapter just returns nothing """
    __implements__ = [ParameterAdapterInterface]

    def getlist(self, name):
        """ :See: `ParameterAdapterInterface.getlist` """
        # pylint: disable = W0613
        return []

    def getfirst(self, name, default=None):
        """ :See: `ParameterAdapterInterface.getfirst` """
        # pylint: disable = W0613
        return default
