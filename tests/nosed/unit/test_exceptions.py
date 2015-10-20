# -*- coding: ascii -*-
r"""
:Copyright:

 Copyright 2014 - 2015
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

===========================
 Tests for tdi._exceptions
===========================

Tests for tdi._exceptions
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"

from nose.tools import assert_raises

from tdi import _exceptions


def test_reraise():
    """ _exceptions.reraise() re-reraises original exception """
    with assert_raises(RuntimeError):
        try:
            raise RuntimeError()
        except RuntimeError:
            with _exceptions.reraise():  # pylint: disable = no-member
                raise ValueError()

    with assert_raises(RuntimeError):
        try:
            raise RuntimeError()
        except RuntimeError:
            with _exceptions.reraise():  # pylint: disable = no-member
                pass
