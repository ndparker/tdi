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

====================================
 Exceptions used in the tdi package
====================================

The module provides all exceptions and warnings used throughout the
`tdi` package.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

import contextlib as _contextlib
import sys as _sys
import warnings as _warnings


@_contextlib.contextmanager
def reraise():
    """ Reraise the currently active exception when exiting the context """
    exc = _sys.exc_info()
    try:
        yield None
    finally:
        raise exc[0], exc[1], exc[2]


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


class DependencyError(Error):
    """ A dependency error occured """


class DependencyCycle(DependencyError):
    """
    Dependencies created a cycle

    The exception argument contains the cycling nodes as a list
    """


class Warning(Warning):
    """
    Base warning for this package

    >>> with _warnings.catch_warnings(record=True) as record:
    ...     Warning.emit('my message')
    ...     assert len(record) == 1
    ...     str(record[0].message)
    'my message'

    >>> _warnings.simplefilter('error')
    >>> Warning.emit('lalala')
    Traceback (most recent call last):
    ...
    Warning: lalala
    """
    # pylint: disable = redefined-builtin, undefined-variable

    @classmethod
    def emit(cls, message, stacklevel=1):  # pragma: no cover
        """
        Emit a warning of this very category

        This method is pure convenience. It saves you the unfriendly
        ``warnings.warn`` syntax (and the ``warnings`` import).

        :Parameters:
          `message` : any
            The warning message

          `stacklevel` : ``int``
            Number of stackframes to go up in order to place the warning
            source. This is useful for generic warning-emitting helper
            functions. The stacklevel of *this* helper function is already
            taken into account.
        """
        # Note that this method cannot be code-covered, probably because of
        # the stack magic.
        _warnings.warn(message, cls, max(1, stacklevel) + 1)


class DeprecationWarning(Warning):  # pylint: disable = redefined-builtin
    """ TDI specific deprecation warning """


class NodeWarning(Warning):
    """ A (non-fatal) inconsistency in the nodetree occured """


class AutoUpdateWarning(Warning):
    """ An auto update error occured after the template was first loaded """
