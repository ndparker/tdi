/*
 * Copyright 2012
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

#ifndef TDI_CONTENT_H
#define TDI_CONTENT_H

#include "cext.h"
#include "tdi.h"

/*
 * content structure
 */
struct tdi_content_t {
    PyObject *clean;         /* clean content */
    PyObject *with_escapes;  /* Content with escape sequences */
};

#define TDI_CONTENT_VISIT(content) do {  \
    tdi_content_t *tmp__ = (content);    \
    if (tmp__) {                         \
        Py_VISIT(tmp__->clean);          \
        Py_VISIT(tmp__->with_escapes);   \
    }                                    \
} while (0)

#define TDI_CONTENT_CLEAR(content) do {   \
    tdi_content_t *tmp__ = (content);     \
    if (tmp__) {                          \
        (content) = NULL;                 \
        Py_XDECREF(tmp__->clean);         \
        Py_XDECREF(tmp__->with_escapes);  \
        PyMem_Free(tmp__);                \
    }                                     \
} while (0)


/*
 * Create new content structure
 */
tdi_content_t *
tdi_content_new(void);


/*
 * Copy content structure
 */
tdi_content_t *
tdi_content_copy(tdi_content_t *);


#endif
