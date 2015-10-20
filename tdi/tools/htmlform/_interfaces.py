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

=====================
 HTML forms reloaded
=====================

Form helper classes.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"
__all__ = [
    'ParameterAdapterInterface', 'PreProcInterface', 'PostProcInterface',
]


class ParameterAdapterInterface(object):
    """
    Interface for a request parameter adapter suitable for `HTMLForm`
    """

    def getlist(self, name):
        """
        Determine all parameters submitted under a name

        :Parameters:
          `name` : ``str``
            The name to look up

        :Return: The List of values (maybe empty) (``[u'value', ...]``)
        :Rtype: ``list``
        """

    def getfirst(self, name, default=None):
        """
        Determine one parameter of all submitted under a name

        It doesn't have to be the first parameter, but it should work
        deterministically, i.e. the method should always return the same
        value for the same name.

        :Parameters:
          `name` : ``str``
            The name to look up

          `default` : ``basestring``
            The returned value if name could not be found

        :Return: The found value. If it was not found, `default` is returned
        :Rtype: ``basestring``
        """


class PreProcInterface(object):
    """ Interface for node processors """

    def __call__(self, method, node, kwargs):
        """
        Pre process the node

        :Parameters:
          `method` : ``str``
            The name of the method (like ``'text'`` or ``'checkbox'``)

          `node` : `tdi.nodetree.Node`
            The node to process

          `kwargs` : ``dict``
            The arguments of the HTMLForm method

        :Return: node and kwargs again (they do not need to be the same as
                 input). Keys appearing in kwargs override the original
                 parameters then. (``(node, kwargs)``)
        :Rtype: ``tuple``
        """


class PostProcInterface(object):
    """ Interface for node processors """

    def __call__(self, method, node, kwargs):
        """
        Post process the node

        :Parameters:
          `method` : ``str``
            The name of the method (like ``'text'`` or ``'checkbox'``)

          `node` : `tdi.nodetree.Node`
            The node to process

          `kwargs` : ``dict``
            The arguments of the HTMLForm method
        """
