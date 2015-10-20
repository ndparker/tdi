#!/usr/bin/env python
# -*- coding: ascii -*-
#
# Copyright 2006 - 2015
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

import sys as _sys
from _setup import run


def setup(args=None, _manifest=0):
    """ Main setup function """
    from _setup.ext import Extension
    from _setup import commands as _commands

    class TDIExtension(Extension):
        def __init__(self, *args, **kwargs):
            Extension.__init__(self, *args, **kwargs)

            macro = ('TDI_AVOID_GC', None)
            self.define_macros.append(macro)
            def finalizer(d, s=self, m=macro):
                if d.with_full_gc:
                    if m in s.define_macros:
                        s.define_macros.remove(m)

            _commands.add_option('install_lib', 'with-full-gc',
                help_text='Enable full garbage collection',
                inherit='install',
            )
            _commands.add_finalizer('install_lib', 'full-gc', finalizer)
            _commands.add_option('build_ext', 'with-full-gc',
                help_text='Enable full garbage collection',
                inherit=('build', 'install_lib'),
            )
            _commands.add_finalizer('build_ext', 'full-gc', finalizer)

    if _sys.version_info[0] == 3:
        # turn off c extension for python3 for now.
        ext = []
    elif 'java' in _sys.platform.lower():
        # no c extension for jython
        ext = None
    elif getattr(_sys, 'pypy_version_info', None) is not None:
        # no experiments for pypy - it may work though (2.0 beta looked
        # promising)
        ext = None
    else:
        ext = [TDIExtension('tdi.c._tdi_impl', [
            'tdi/c/main.c',

            'tdi/c/lib/content.c',
            'tdi/c/lib/copy.c',
            'tdi/c/lib/finalize.c',
            'tdi/c/lib/globals.c',
            'tdi/c/lib/iterate.c',
            'tdi/c/lib/overlay.c',
            'tdi/c/lib/remove.c',
            'tdi/c/lib/render.c',
            'tdi/c/lib/repeat.c',
            'tdi/c/lib/replace.c',
            'tdi/c/lib/repr.c',
            'tdi/c/lib/scope.c',
            'tdi/c/lib/util.c',

            'tdi/c/lib/markup/soup_lexer.c',
            'tdi/c/lib/markup/soup_parser.c',

            'tdi/c/attr.c',
            'tdi/c/attribute_analyzer.c',
            'tdi/c/base_event_filter.c',
            'tdi/c/decoder_wrapper.c',
            'tdi/c/encoder_wrapper.c',
            'tdi/c/htmldecode.c',
            'tdi/c/html_decoder.c',
            'tdi/c/iterate_iterator.c',
            'tdi/c/model_adapters.c',
            'tdi/c/node.c',
            'tdi/c/raw_node.c',
            'tdi/c/render_iterator.c',
            'tdi/c/repeat_iterator.c',
            'tdi/c/repr_iterator.c',
            'tdi/c/root_node.c',
            'tdi/c/soup_encoder.c',
            'tdi/c/soup_encoding_detect_filter.c',
            'tdi/c/soup_lexer.c',
            'tdi/c/soup_parser.c',
            'tdi/c/template_node.c',
            'tdi/c/text_decoder.c',
            'tdi/c/text_encoder.c',
            'tdi/c/xml_decoder.c',
        ], depends=[
            '_setup/include/cext.h',

            'tdi/c/lib/include/tdi.h',
            'tdi/c/lib/include/tdi_content.h',
            'tdi/c/lib/include/tdi_copy.h',
            'tdi/c/lib/include/tdi_exceptions.h',
            'tdi/c/lib/include/tdi_finalize.h',
            'tdi/c/lib/include/tdi_globals.h',
            'tdi/c/lib/include/tdi_iterate.h',
            'tdi/c/lib/include/tdi_node_clear.h',
            'tdi/c/lib/include/tdi_overlay.h',
            'tdi/c/lib/include/tdi_remove.h',
            'tdi/c/lib/include/tdi_render.h',
            'tdi/c/lib/include/tdi_repeat.h',
            'tdi/c/lib/include/tdi_replace.h',
            'tdi/c/lib/include/tdi_repr.h',
            'tdi/c/lib/include/tdi_scope.h',
            'tdi/c/lib/include/tdi_util.h',

            'tdi/c/lib/include/tdi_lexer.h',
            'tdi/c/lib/include/tdi_soup_lexer.h',
            'tdi/c/lib/include/tdi_parser.h',
            'tdi/c/lib/include/tdi_soup_parser.h',

            'tdi/c/include/htmldecode.h',
            'tdi/c/include/obj_attr.h',
            'tdi/c/include/obj_attribute_analyzer.h',
            'tdi/c/include/obj_avoid_gc.h',
            'tdi/c/include/obj_base_event_filter.h',
            'tdi/c/include/obj_decoder.h',
            'tdi/c/include/obj_encoder.h',
            'tdi/c/include/obj_html_decoder.h',
            'tdi/c/include/obj_iterate_iter.h',
            'tdi/c/include/obj_model_adapters.h',
            'tdi/c/include/obj_node.h',
            'tdi/c/include/obj_raw_node.h',
            'tdi/c/include/obj_render_iter.h',
            'tdi/c/include/obj_repeat_iter.h',
            'tdi/c/include/obj_repr_iter.h',
            'tdi/c/include/obj_root_node.h',
            'tdi/c/include/obj_soup_encoder.h',
            'tdi/c/include/obj_soup_encoding_detect_filter.h',
            'tdi/c/include/obj_soup_lexer.h',
            'tdi/c/include/obj_soup_parser.h',
            'tdi/c/include/obj_template_node.h',
            'tdi/c/include/obj_text_decoder.h',
            'tdi/c/include/obj_text_encoder.h',
            'tdi/c/include/obj_xml_decoder.h',
        ], include_dirs=[
            'tdi/c/include',
            'tdi/c/lib/include',
        ])]

    if ext is not None:
        ext.extend([
            Extension('tdi.c._tdi_rjsmin', sources=['tdi/c/rjsmin.c']),
            Extension('tdi.c._tdi_rcssmin', sources=['tdi/c/rcssmin.c']),
        ])

    return run(
        ext=ext,
        script_args=args,
        manifest_only=_manifest,
    )


def manifest():
    """ Create List of packaged files """
    return setup((), _manifest=1)


if __name__ == '__main__':
    setup()
