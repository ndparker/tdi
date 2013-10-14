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

#ifndef TDI_SCOPE_H
#define TDI_SCOPE_H

#include "cext.h"
#include "tdi.h"

/*
 * Scope struct
 */
struct tdi_scope_t {
    PyObject *name;   /* Scope name */

    int is_hidden;    /* is hidden? */
    int is_absolute;  /* is absolute */
};


#define TDI_SCOPE_VISIT(scope) do { \
    if (scope)                      \
        Py_VISIT((scope)->name);    \
} while (0)

#define TDI_SCOPE_CLEAR(scope) do {   \
    if (scope) {                      \
        tdi_scope_t *tmp__ = (scope); \
        (scope) = NULL;               \
        Py_DECREF(tmp__->name);       \
        PyMem_Free(tmp__);            \
    }                                 \
} while (0)


/*
 * Allocate new tdi_scope_t struct
 */
tdi_scope_t *
tdi_scope_new(PyObject *name, int hidden, int absolute);


/*
 * Copy scope struct
 */
tdi_scope_t *
tdi_scope_copy(tdi_scope_t *scope);


#endif
