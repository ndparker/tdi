#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi import filters as _filters
from tdi import html as _html

class Count(_filters.BaseEventFilter):
    def __init__(self, builder):
        super(Count, self).__init__(builder)
        self.tags = {}

    def handle_starttag(self, name, attr, closed, data):
        self.tags[name] = self.tags.get(name, 0) + 1
        self.builder.handle_starttag(name, attr, closed, data)

    def finalize(self):
        keys = self.tags.keys()
        keys.sort()
        for key in keys:
            print "%s: %d" % (key, self.tags[key])
        return self.builder.finalize()

html = _html.replace(overlay_eventfilters=[Count])

print "Before Loading"
template = html.from_string("""
<anode tdi:overlay="foo"></anode>
""").overlay(html.from_string("""
<bnode tdi:overlay="foo">
<cnode />
</bnode>
"""))

print ">>> Between Loading and Rendering"

template.render()

print ">>> Between Rendering"

template.render()

print ">>> After Rendering"
