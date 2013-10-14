#!/usr/bin/env python
import warnings as _warnings
_warnings.resetwarnings()
_warnings.filterwarnings('error')

from tdi.integration import wtf_service as _wtf_service

class Param(object):
    def multi(self, name):
        return []
param = Param()

adapter = _wtf_service.RequestParameterAdapter(param)
print adapter.getlist == param.multi

class Inherited(_wtf_service.RequestParameterAdapter):
    pass

adapter = Inherited(param)
print adapter.getlist == param.multi
