/*
 * Copyright 2014
 * Andr\xe9 Malo or his licensors, as applicable
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef TDI_OBJ_PRERENDER_WRAPPER_H
#define TDI_OBJ_PRERENDER_WRAPPER_H

#include "cext.h"
#include "tdi.h"


typedef struct tdi_prerender_wrapper_t tdi_prerender_wrapper_t;

extern PyTypeObject TDI_PreRenderWrapperType;

#define TDI_PreRenderWrapperType_Check(op) \
    PyObject_TypeCheck(op, &TDI_PreRenderWrapperType)

#define TDI_PreRenderWrapperType_CheckExact(op) \
    ((op)->ob_type == &TDI_PreRenderWrapperType)


PyObject *
tdi_prerender_wrapper_factory(tdi_prerender_wrapper_t *, PyObject *);

PyObject *
tdi_prerender_wrapper_new(PyTypeObject *, PyObject *, PyObject *, int);

#endif
