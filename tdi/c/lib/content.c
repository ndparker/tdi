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

#include "cext.h"
#include "tdi.h"
#include "tdi_content.h"


/*
 * Allocate new content structure
 */
tdi_content_t *
tdi_content_new(void)
{
    tdi_content_t *content;

    if (!(content = PyMem_Malloc(sizeof *content)))
        return NULL;

    content->clean = NULL;
    content->with_escapes = NULL;
    return content;
}


/*
 * Copy existing content structure
 */
tdi_content_t *
tdi_content_copy(tdi_content_t *content)
{
    tdi_content_t *result;

    if (!content)
        return NULL;

    if (!(result = tdi_content_new()))
        return NULL;

    result->clean = content->clean;
    Py_XINCREF(result->clean);
    result->with_escapes = content->with_escapes;
    Py_XINCREF(result->with_escapes);

    return result;
}
