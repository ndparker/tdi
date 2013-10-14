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
#include "tdi_remove.h"

#include "obj_node.h"


/*
 * Mark node as removed
 */
void
tdi_remove_node(tdi_node_t *node)
{
    node->flags |= NODE_REMOVED;

    Py_INCREF(tdi_g_empty_dict);
    Py_CLEAR(node->namedict);
    node->namedict = tdi_g_empty_dict;
}
