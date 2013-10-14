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
====================================
 Exceptions used in the tdi package
====================================

The module provides all exceptions and warnings used throughout the
`tdi` package.
"""
__author__ = u"Andr\xe9 Malo"
__docformat__ = "restructuredtext en"

import warnings as _warnings


class Error(Exception):
    """ Base exception for this package """


class TemplateError(Error):
    """ Error in a template """

class TemplateEncodingError(TemplateError):
    """ Template encoding error """

class TemplateAttributeError(TemplateError):
    """ A tdi attribute could not be parsed """

class TemplateAttributeEmptyError(TemplateAttributeError):
    """ A tdi attribute was empty """

class TemplateReloadError(TemplateError):
    """ Error during template reload """

class TemplateFactoryError(TemplateError):
    """ Template factory misuse """

class OverlayError(TemplateError):
    """ Error in overlay work """


class NodeError(Error):
    """ Error in node processing """

class NodeTreeError(NodeError):
    """ The node tree was tried to be modified after it was finalized """

class NodeNotFoundError(NodeError):
    """ node was not found """


class ModelError(Error):
    """ Base error for model errors """

class ModelMissingError(ModelError):
    """ A required model method was missing """


class LexerError(Error):
    """ Lexer Error """

class LexerEOFError(LexerError):
    """ Unexpected EOF """

class LexerStateError(LexerError):
    """ Invalid state change """

class LexerFinalizedError(LexerStateError):
    """ Lexer was already finalized """


class Warning(Warning): # pylint: disable = W0622
    """ Base warning for this package """

    def emit(cls, message, stacklevel=1):
        """ Emit a warning of this very category """
        _warnings.warn(message, cls, max(1, stacklevel) + 1)
    emit = classmethod(emit)


class DeprecationWarning(Warning): # pylint: disable = W0622
    """ TDI specific deprecation warning """

class NodeWarning(Warning):
    """ A (non-fatal) inconsistency in the nodetree occured """

class AutoUpdateWarning(Warning):
    """ An auto update error occured after the template was first loaded """
