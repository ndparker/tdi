#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

# BEGIN INCLUDE
from tdi import html
from tdi.tools.html import decode

# This is some typcial flash embedding code.
# It serves as a "layout widget", placed via overlay
flash = html.from_string("""
<!-- <tdi> is used as neutral dummy element (removed due to the - flag) -->
<tdi tdi:scope="-flash" tdi:overlay="<-flash">
    <object tdi="object_ie"
        classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" width=""
        height="">
        <param tdi="url" name="movie" value="" />
        <param tdi="param" />
        <![if !IE]><object tdi="object_other"
            type="application/x-shockwave-flash" data="" width="" height="">
            <param tdi="param" />
        <![endif]>
        <p tdi="alternative">You need to enable <a
          href="http://www.adobe.com/go/getflashplayer">Flash</a> to view this
          content.</p>
    <![if !IE]></object><![endif]></object>
</tdi>
""")

# page template, using the flash layout widget, passing parameters
template = html.from_string("""
<html>
<body>
    <h1>some flash</h1>
    <tdi tdi:scope="-flash.param" tdi="-init"
            file="flashfile.swf" width="400" height="300">
        <tdi tdi="param" name="bgcolor" value="#ffffff" />
        <tdi tdi="param" name="wmode" value="transparent" />
        <tdi tdi="param" name="quality" value="high" />
        <img tdi="alternative" src="replacement-image.png" alt="some cool text" />
    </tdi>
    <tdi tdi:overlay="->flash" />
</body>
</html>
""".lstrip()).overlay(flash)


class FlashParam(dict):
    def render_init(self, node):
        self.clear()
        encoding = node.raw.encoder.encoding
        self['file'] = decode(node[u'file'], encoding)
        self['width'] = decode(node[u'width'], encoding)
        self['height'] = decode(node[u'height'], encoding)
        self['param'] = []
        node.render()
        node.remove()

    def render_param(self, node):
        encoding = node.raw.encoder.encoding
        self['param'].append((
            decode(node[u'name'], encoding),
            decode(node[u'value'], encoding),
        ))

    def render_alternative(self, node):
        self['alt'] = node.copy()


class Flash(object):
    def __init__(self):
        self.scope_param = FlashParam()

    def render_object_ie(self, node):
        p = self.scope_param
        node[u'width'] = p['width']
        node[u'height'] = p['height']

    def render_url(self, node):
        p = self.scope_param
        node[u'value'] = p['file']

    def render_param(self, node):
        p = self.scope_param
        for pnode, (name, value) in node.iterate(p['param']):
            pnode[u'name'] = name
            pnode[u'value'] = value

    def render_object_other(self, node):
        p = self.scope_param
        node[u'width'] = p['width']
        node[u'height'] = p['height']
        node[u'data'] = p['file']

    def render_alternative(self, node):
        p = self.scope_param
        if 'alt' in p:
            node.replace(None, p['alt'])


class Model(object):
    def __init__(self):
        self.scope_flash = Flash()


template.render(Model())
