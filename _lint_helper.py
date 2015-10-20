# -*- encoding: utf-8 -*-
"""
Lint Helper
~~~~~~~~~~~

"""

import astroid as _astroid


def register(_):
    "Nop"
    pass


# stolen from here: https://gist.github.com/OddBloke/6681727
from nose import tools as _nose_tools  # pylint: disable = E0611
_astroid.builder.AstroidBuilder(_astroid.MANAGER).string_build(
    ''.join([
        "def %s(*args, **kwargs):\n    pass\n" % (func_name,)
        # pylint: disable=no-member
        for func_name in _nose_tools.__all__
    ]),
    modname='nose.tools'
)
