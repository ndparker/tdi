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

#ifndef TDI_REPLACE_H
#define TDI_REPLACE_H

#include "cext.h"
#include "tdi.h"

/*
 * Replace node with another one
 */
int
tdi_replace_node(tdi_node_t *self, tdi_node_t *other, PyObject *callback,
                 PyObject *fixed);


#endif
