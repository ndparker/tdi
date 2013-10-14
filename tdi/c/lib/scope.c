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

#include "cext.h"
#include "tdi_scope.h"


/*
 * Copy scope struct
 */
tdi_scope_t *
tdi_scope_copy(tdi_scope_t *scope)
{
    tdi_scope_t *new_scope;

    if (!scope)
        return NULL;
    if (!(new_scope = PyMem_Malloc(sizeof *new_scope))) {
        PyErr_NoMemory();
        return NULL;
    }

    Py_INCREF(scope->name);
    new_scope->name = scope->name;
    new_scope->is_hidden = scope->is_hidden;
    new_scope->is_absolute = scope->is_absolute;

    return new_scope;
}

/*
 * Allocate new tdi_scope_t struct
 */
tdi_scope_t *
tdi_scope_new(PyObject *name, int hidden, int absolute)
{
    tdi_scope_t *new_scope;

    if (!(new_scope = PyMem_Malloc(sizeof *new_scope))) {
        Py_DECREF(name);
        PyErr_NoMemory();
        return NULL;
    }

    new_scope->name = name;
    new_scope->is_hidden = hidden;
    new_scope->is_absolute = absolute;

    return new_scope;
}
