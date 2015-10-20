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

========================
 Version Representation
========================

Version representation.
"""
if __doc__:
    # pylint: disable = redefined-builtin
    __doc__ = __doc__.encode('ascii').decode('unicode_escape')
__author__ = r"Andr\xe9 Malo".encode('ascii').decode('unicode_escape')
__docformat__ = "restructuredtext en"


class Version(tuple):
    """
    Container representing the package version

    :IVariables:
      `major` : ``int``
        The major version number

      `minor` : ``int``
        The minor version number

      `patch` : ``int``
        The patch level version number

      `is_dev` : ``bool``
        Is it a development version?

      `revision` : ``int``
        Internal revision
    """
    _str = "(unknown)"

    def __new__(cls, versionstring, is_dev, revision):
        """
        Construction

        :Parameters:
          `versionstring` : ``str``
            The numbered version string (like ``"1.1.0"``)
            It should contain at least three dot separated numbers

          `is_dev` : ``bool``
            Is it a development version?

          `revision` : ``int``
            Internal revision

        :Return: New version instance
        :Rtype: `version`
        """
        # pylint: disable = unused-argument

        tup = []
        versionstring = versionstring.strip()
        isuni = isinstance(versionstring, unicode)
        strs = []
        if versionstring:
            for item in versionstring.split('.'):
                try:
                    item = int(item)
                    strs.append(str(item))
                except ValueError:
                    if isuni:
                        strs.append(item.encode('utf-8'))
                    else:
                        try:
                            item = item.decode('ascii')
                            strs.append(item.encode('ascii'))
                        except UnicodeError:
                            try:
                                item = item.decode('utf-8')
                                strs.append(item.encode('utf-8'))
                            except UnicodeError:
                                strs.append(item)
                                item = item.decode('latin-1')
                tup.append(item)
        while len(tup) < 3:
            tup.append(0)
        self = tuple.__new__(cls, tup)
        self._str = ".".join(strs)  # pylint: disable = protected-access
        return self

    def __init__(self, versionstring, is_dev, revision):
        """
        Initialization

        :Parameters:
          `versionstring` : ``str``
            The numbered version string (like ``1.1.0``)
            It should contain at least three dot separated numbers

          `is_dev` : ``bool``
            Is it a development version?

          `revision` : ``int``
            Internal revision
        """
        # pylint: disable = unused-argument

        super(Version, self).__init__()
        self.major, self.minor, self.patch = self[:3]
        self.is_dev = bool(is_dev)
        self.revision = int(revision)

    def __repr__(self):
        """
        Create a development string representation

        :Return: The string representation
        :Rtype: ``str``
        """
        return "%s.%s(%r, is_dev=%r, revision=%r)" % (
            self.__class__.__module__,
            self.__class__.__name__,
            self._str,
            self.is_dev,
            self.revision,
        )

    def __str__(self):
        """
        Create a version like string representation

        :Return: The string representation
        :Rtype: ``str``
        """
        return "%s%s" % (
            self._str,
            ("", "-dev-r%d" % self.revision)[self.is_dev],
        )

    def __unicode__(self):
        """
        Create a version like unicode representation

        :Return: The unicode representation
        :Rtype: ``unicode``
        """
        return u"%s%s" % (
            u".".join(map(unicode, self)),
            (u"", u"-dev-r%d" % self.revision)[self.is_dev],
        )
