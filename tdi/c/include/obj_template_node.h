/*
 * Copyright 2010
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

#ifndef TDI_OBJ_TEMPLATE_NODE_H
#define TDI_OBJ_TEMPLATE_NODE_H

#include "cext.h"

extern PyTypeObject TDI_TemplateNodeType;

#define TDI_TemplateNodeType_Check(op) \
    PyObject_TypeCheck(op, &TDI_TemplateNodeType)

#define TDI_TemplateNodeType_CheckExact(op) \
    ((op)->ob_type == &TDI_TemplateNodeType)


PyObject *
tdi_template_node_text_new(PyObject *content);


PyObject *
tdi_template_node_escaped_text_new(PyObject *escaped, PyObject *content);


/*
 * Allocate new TDI_TemplateNodeType and initialize as proc node
 */
PyObject *
tdi_template_node_template_new(PyObject *tagname, PyObject *attr,
                               PyObject *special, int is_closed);


#endif
