/*
 * Copyright 2006 - 2012
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
#include "tdi_copy.h"
#include "tdi_replace.h"

#include "obj_node.h"

/*
 * make replaced callback args
 */
static PyObject *
make_replaced_callback_args(PyObject *fixed)
{
    PyObject *args, *tmp;
    Py_ssize_t length, j;

    length = fixed ? PyTuple_GET_SIZE(fixed) : 0;
    if (!(args = PyTuple_New(length)))
        return NULL;

    for (j = 0; j < length; ++j) {
        tmp = PyTuple_GET_ITEM(fixed, j);
        Py_INCREF(tmp);
        PyTuple_SET_ITEM(args, j, tmp);
    }

    return args;
}


/*
 * Replace node with another one
 */
int
tdi_replace_node(tdi_node_t *self, tdi_node_t *other,
                 PyObject *callback, PyObject *fixed)
{
    PyObject *result, *name;

    name = self->name;
    Py_XINCREF(name);
    if (!(result = tdi_node_deepcopy(other, self->model, self->ctx, self))) {
        Py_XDECREF(name);
        return -1;
    }
    Py_DECREF(result);

    Py_CLEAR(self->name);
    self->name = name;

    Py_INCREF(callback);
    Py_CLEAR(self->callback);
    self->callback = callback;

    Py_CLEAR(self->overlays);
    if (!(self->overlays = make_replaced_callback_args(fixed)))
        return -1;

    self->kind = CB_NODE;

    return 0;
}
