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

#ifndef TDI_OBJ_ATTR_H
#define TDI_OBJ_ATTR_H

#include "cext.h"
#include "tdi.h"

/*
 * Single value in attribute dicts
 */
struct tdi_attr_t {
    PyObject_HEAD

    PyObject *key;    /* original cased key */
    PyObject *value;  /* value */
};


extern PyTypeObject TDI_AttrType;


/*
 * Allocate new AttrType and initialize.
 */
PyObject *
tdi_attr_new(PyObject *key, PyObject *value);


#endif
