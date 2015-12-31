.. -*- coding: utf-8 -*-

================================================
 TDI - The next evolutional step for templating
================================================

TABLE OF CONTENTS
-----------------

1. Introduction
2. Copyright and License
3. System Requirements
4. Installation
5. Documentation
6. Bugs
7. Author Information


INTRODUCTION
------------

TDI (Template Data Interface) is a markup templating system written in python
with optional speedup code written in C. Unlike most templating systems the
TDI does not invent its own language to provide functionality. Instead you
simply mark the nodes you want to manipulate within the template document. The
template is parsed and the marked nodes are presented to your python code,
where they can be modified in any way you want.


COPYRIGHT AND LICENSE
---------------------

Copyright 2006 - 2014
André Malo or his licensors, as applicable.

The whole package is distributed under the Apache License Version 2.0.
You'll find a copy in the root directory of the distribution or online
at: <http://www.apache.org/licenses/LICENSE-2.0>.


SYSTEM REQUIREMENTS
-------------------

You need python 2 (>= 2.7). Python 3 is NOT supported yet.

The following python implementations are supported, too:

- PyPy (2.0)
- Jython (2.7)


INSTALLATION
------------

TDI is set up using the standard python distutils. So you can install
it using the usual command:

$ python setup.py install

The command above will install a new "tdi" package into python's
library path.

Additionally it will install the documentation. On unices it will be
installed by default into <prefix>/share/doc/tdi.

For customization options please study the output of

$ python setup.py --help


DOCUMENTATION
-------------

You'll find a user documentation in the docs/userdoc/ directory of the
distribution package. It is installed by default under <prefix>/share/doc/tdi
(e.g. /usr/share/doc/tdi). Further, there's the code documentation, generated
by epydoc (<http://epydoc.sourceforge.net/>), which can be found in the
docs/apidoc/ subdirectory.

The latest documentation is also available online at
<http://opensource.perlig.de/tdi/>.


BUGS
----

No bugs, of course. ;-)
But if you've found one or have an idea how to improve the TDI, feel free
to send a pull request on `github <https://github.com/ndparker/tdi>`_
or send a mail to <tdi-bugs@perlig.de>.


AUTHOR INFORMATION
------------------

André "nd" Malo <nd@perlig.de>
GPG: 0x8103A37E


  If God intended people to be naked, they would be born that way.
                                                   -- Oscar Wilde
