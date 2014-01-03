/*
 * Copyright 2010 - 2014
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

#ifndef TDI_OBJ_RENDER_ADAPTER_H
#define TDI_OBJ_RENDER_ADAPTER_H

#include "cext.h"
#include "tdi.h"


extern PyTypeObject TDI_RenderAdapterType;

#define TDI_RenderAdapterType_Check(op) \
    PyObject_TypeCheck(op, &TDI_RenderAdapterType)

#define TDI_RenderAdapterType_CheckExact(op) \
    ((op)->ob_type == &TDI_RenderAdapterType)


/*
 * Find a model method
 */
PyObject *
tdi_render_adapter_method(tdi_adapter_t *, PyObject *, PyObject *, PyObject *,
                          int);


/*
 * Create new adapter from adapter with a new model
 */
PyObject *
tdi_render_adapter_factory(tdi_adapter_t *self, PyObject *model);


/*
 * Create new model adapter
 */
PyObject *
tdi_adapter_new(PyTypeObject *, PyObject *, int, int, int);


/*
 * Create model object from alien model
 */
PyObject *
tdi_adapter_new_alien(PyObject *);


/*
 * Return emit_escaped flag
 */
int
tdi_adapter_emit_escaped(tdi_adapter_t *);


#endif
