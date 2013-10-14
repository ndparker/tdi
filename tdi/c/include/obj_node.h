/*
 * Copyright 2010 - 2013
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

#ifndef TDI_OBJ_NODE_H
#define TDI_OBJ_NODE_H

#include "cext.h"

#include "tdi.h"

/*
 * Different node types that may appear in the node lists
 */
typedef enum {
    TEXT_NODE,  /* unprocessed text node (just written to the stream) */
    PROC_NODE,  /* processable node */
    SEP_NODE,   /* separator node */
    CB_NODE,    /* callback node */
    DONE_NODE   /* already processed node */
} nodekind;

/*
 * Common object structure for all 3 kinds of nodes types
 * (Node, TemplateNode and Root)
 *
 * Not all fields are always filled, but the common structure makes it
 * *very* easy to copy data between the types.
 *
 * RootType only knows about nodes, namedict, content and overlay.
 * TemplateNodeType misses callback, model and ctx.
 * NodeType misses overlay and doesn't care about the finalized flag.
 */
struct tdi_node_t {
    PyObject_HEAD
    PyObject      *weakreflist;

    PyObject      *sep;           /* separator node (or NULL) */
    PyObject      *callback;      /* callback callable (or NULL) */
    PyObject      *nodes;         /* list of subnodes (PyList) */
    PyObject      *namedict;      /* name->index mapping of direct subnodes */
    PyObject      *tagname;       /* tagname of the node */
    PyObject      *attr;          /* attribute dict of the node */
    PyObject      *endtag;        /* endtag string of the node */
    PyObject      *name;          /* name of the node (or NULL) */
    PyObject      *ctx;           /* node context (or NULL) */
    PyObject      *overlays;      /* Overlay mapping (for root nodes)
                                   * alternative use: callback parameter tuple
                                   * alternative use: repetition parameter tuple
                                   */
    PyObject      *modelscope;    /* Scope passed to the model */
    tdi_content_t *content;       /* text content of the node (or NULL) */
    PyObject      *complete;      /* pre-rendered separator node content
                                   * (or NULL)
                                   */
    tdi_overlay_t *overlay;       /* Overlay info (or NULL) */
    tdi_scope_t   *scope;         /* Scope info (or NULL) */
    tdi_encoder_t *encoder;       /* output encoder */
    tdi_decoder_t *decoder;       /* input decoder */
    tdi_adapter_t *model;         /* model instance */
    int flags;                    /* node flags */
    nodekind kind;                /* node kind */
};

/* node flags */
#define NODE_CLOSED    (1 << 0)  /* is the tag self closing? */
#define NODE_REMOVED   (1 << 1)  /* was the node removed? */
#define NODE_NOELEMENT (1 << 2)  /* should surrounding element be omitted? */
#define NODE_FINALIZED (1 << 3)  /* was the node finalized? */
#define NODE_USER      (1 << 4)  /* user node? (vs. template node) */
#define NODE_REPEATED  (1 << 5)  /* node to be repeated? */
#define NODE_MASKED    (1 << 6)  /* node is masked */
#define NODE_ROOT      (1 << 7)  /* is root node? */
#define NODE_NOAUTO    (1 << 8)  /* Don't call render method automatically? */
#define NODE_NEWATTR   (1 << 9)  /* Attributes are new? (need to be decoded) */


extern PyTypeObject TDI_NodeType;


#endif
