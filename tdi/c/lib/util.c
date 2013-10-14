/*
 * Copyright 2006, 2007, 2008, 2009, 2010
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
#include "tdi_globals.h"
#include "tdi_exceptions.h"
#include "tdi_copy.h"
#include "tdi_util.h"

#include "obj_node.h"


/*
 * fast lowercase (without Python machine overhead)
 */
PyObject *
tdi_util_tolower(PyObject *string)
{
    PyObject *result;
    char *cresult, *cstring;
    Py_ssize_t size;
    int c;

    size = PyString_GET_SIZE(string);
    if (!(result = PyString_FromStringAndSize(NULL, size)))
        return NULL;
    cresult = PyString_AS_STRING(result);
    cstring = PyString_AS_STRING(string);

    while (size--) {
        c = Py_CHARMASK(*cstring++);
        *cresult++ = isupper(c) ? tolower(c) : c;
    }

    return result;
}


/*
 * determine direct subnode of NodeType
 */
PyObject *
tdi_util_subnode(tdi_node_t *self, PyObject *name)
{
    PyObject *tmp, *nodes;
    tdi_node_t *node;
    Py_ssize_t idx;

    node = self;
    Py_INCREF(node);
    do {
        if (!(tmp = PyDict_GetItem(node->namedict, name))) {
            if (!PyErr_Occurred())
                PyErr_SetObject(TDI_E_NodeNotFoundError, name);
            Py_DECREF(node);
            return NULL;
        }
        idx = PyInt_AsSsize_t(tmp);
        if (PyErr_Occurred()) {
            Py_DECREF(node);
            return NULL;
        }
        nodes = node->nodes;
        Py_DECREF(node);
        if (!(node = (tdi_node_t *)PyList_GetItem(nodes,
                                                  idx < 0 ? (-1 - idx): idx)))
            return NULL;

        Py_INCREF(node);
        if (!(tmp = tdi_node_copy(node, self->model, self->ctx, 1, NULL))) {
            Py_DECREF(node);
            return NULL;
        }
        if (tmp != (PyObject *)node) {
            Py_INCREF(tmp);
            if (PyList_SetItem(nodes, idx < 0 ? (-1 - idx) : idx, tmp) == -1) {
                Py_DECREF(tmp);
                Py_DECREF(node);
                return NULL;
            }
        }
        Py_DECREF(node);
        if (idx >= 0)
            return tmp;
        node = (tdi_node_t *)tmp;
    } while (1);
}
