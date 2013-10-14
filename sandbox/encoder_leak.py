#!/usr/bin/env python

import time
import os
import sys
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
print os.getpid()

class _tdi(object):
    from tdi import html as html_factory
    from tdi.tools import javascript
    from tdi.tools import css
    from tdi.tools import html

x = u'<h2>Ski-Hotels Schweiz</h2>\r\n<p class="intro">Eine Skih&uuml;tte im Skigebiet Gstaad Mountain Rides, ein Hotel in Saas  Grund, eine Ferienwohnung im Skigebiet Lauchernalp oder eine Pension  Crans Montana &ndash; hier finden Sie die passende Unterkunft f&uuml;r Ihren  Winterurlaub in der Schweiz. Ob nur wenige Gehminuten zum Lift, in der N&auml;he einer Loipe, einen  Skikeller und Wellness-Bereich im Haus &ndash; fragen Sie &Uuml;bernachtungspreise  und freie Zeitr&auml;ume hier an.</p>'
u'<h2>Ski-Hotels Tschechien</h2>\r\n<p class="intro">Ein Appartement im Skigebiet Spindlerm&uuml;hle, ein Hotel in Harrachov oder eine Pension in Petzer &ndash; hier finden Sie die passende Unterkunft f&uuml;r Ihren Winterurlaub in Tschechien. Ob nur wenige Gehminuten zum Lift, eine Skibushaltestelle in der N&auml;he,  einen Skikeller und Wellness-Bereich im Haus &ndash; fragen Sie &Uuml;bernachtungspreise und freie Zeitr&auml;ume hier an.</p>'

x = x.encode('utf-8')
f = _tdi.html_factory.replace(eventfilters=[
    #_tdi.javascript.MinifyFilter,
    #_tdi.css.MinifyFilter,
    _tdi.html.MinifyFilter,
])

while True:
    for _ in xrange(100000):
        f.from_string(x)
    time.sleep(1)


# while ps fuax | grep '[e]ncoder_leak.py' && sleep 1; do :; done | tee out
