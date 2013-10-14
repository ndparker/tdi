#!/usr/bin/env python

import time
import os
import sys
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
print os.getpid()

from tdi.markup.soup import parser, decoder, encoder
from tdi import nodetree
from tdi import html


class Listener(object):
    decoder = decoder.HTMLDecoder('latin-1')
    def handle_starttag(self, name, attrs, closed, data):
        print locals()

    def handle_endtag(self, name, data):
        print locals()


while True:
    for _ in xrange(100000):
        r = nodetree.Root()
        x = r.append_node('z', [], {'attribute': ('', 'a')}, False)
        x.endtag = '</z>'
        r.finalize(encoder.SoupEncoder('latin-1'),
        decoder.HTMLDecoder('latin-1'))
        #p = parser.DEFAULT_PARSER.html(Listener())
        #p.feed('<z tdi="a"></z>')
        #p.finalize()
        #sys.exit()
        #html.from_string('<z tdi="a"></z>')
    time.sleep(1)
