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

#ifndef TDI_OVERLAY_H
#define TDI_OVERLAY_H

#include "cext.h"
#include "tdi.h"

/*
 * Overlay struct
 */
struct tdi_overlay_t {
    PyObject *name;  /* Overlay name */

    int is_hidden;   /* is hidden? */
    int is_target;   /* is only target? */
    int is_source;   /* is only source? */
};


#define TDI_OVERLAY_VISIT(overlay) do { \
    if (overlay)                        \
        Py_VISIT((overlay)->name);      \
} while (0)

#define TDI_OVERLAY_CLEAR(overlay) do {   \
    if (overlay) {                        \
        tdi_overlay_t *tmp__ = (overlay); \
        (overlay) = NULL;                 \
        Py_DECREF(tmp__->name);           \
        PyMem_Free(tmp__);                \
    }                                     \
} while (0)


/*
 * Allocate new tdi_overlay_t struct
 */
tdi_overlay_t *
tdi_overlay_new(PyObject *name, int hidden, int source, int target);


/*
 * Copy overlay struct
 */
tdi_overlay_t *
tdi_overlay_copy(tdi_overlay_t *overlay);


/*
 * Do overlay
 */
tdi_node_t *
tdi_overlay_do(tdi_node_t *root, PyObject *oindex);


#endif
