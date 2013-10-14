#!/usr/bin/env python

HUGE = 10000000
HUGE = 1000000
#HUGE = 1000

from tdi.template import html
#import gc; gc.disable()

template = html.from_string("""<node tdi="item"></node>""")


class DevNull(object):
    def write(self, s):
        pass


class Model(object):
    def render_item(self, node):
        node.repeat(self.repeat_item, xrange(HUGE))

    def repeat_item(self, node, item):
        pass #node.content = unicode(item)


model = Model()
template.render(model, DevNull())
