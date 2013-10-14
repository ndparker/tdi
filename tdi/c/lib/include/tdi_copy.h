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

#ifndef TDI_COPY_H
#define TDI_COPY_H

#include "cext.h"
#include "tdi.h"

/*
 * Allocate new TDI_NodeType and initialize from another Node or TemplateNode
 */
PyObject *
tdi_node_copy(tdi_node_t *node, tdi_adapter_t *model, PyObject *ctx,
              int light, tdi_node_t *target);


/*
 * Deep-copy TDI_NodeType (but shallow-copy TemplateNodeType subnodes)
 */
PyObject *
tdi_node_deepcopy(tdi_node_t *self, tdi_adapter_t *model, PyObject *ctx,
                  tdi_node_t *node);

#endif
