/*
 * Copyright 2013
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

#include "tdi_soup_lexer.h"
#include "tdi_soup_parser.h"

/* -------------------------- BEGIN DECLARATIONS ------------------------- */

typedef struct tagstack {
    struct tagstack *next;
    PyObject *normname;
    PyObject *name;
} tagstack;

struct tdi_soup_parser {
    /* Last error, to be evaluated by the caller */
    tdi_parser_error last_error;

    /* Lexer */
    tdi_soup_lexer *lexer;

    /* Event receiver */
    tdi_parser_callback *cb;
    void *cb_ctx;

    /* Nestable cb */
    tdi_soup_parser_nestable_callback *nestable;
    void *nestable_ctx;

    /* cdata cb */
    tdi_soup_parser_cdata_callback *cdata;
    void *cdata_ctx;

    /* empty cb */
    tdi_soup_parser_empty_callback *empty;
    void *empty_ctx;

    /* normalize cb */
    tdi_soup_parser_normalize_callback *normalize;
    void *normalize_ctx;

    /* Parser state stuff */
    tagstack *tagstack;
    PyObject *lastopen;
    int inempty;
};

/* --------------------------- END DECLARATIONS -------------------------- */

/* ---------------------- BEGIN tagstack DEFINITION ---------------------- */

static int
tagstack_push(tagstack **stack_, PyObject *normname, PyObject *name)
{
    tagstack *stack;

    if (!(stack = PyMem_Malloc(sizeof *stack)))
        return -1;

    stack->normname = (Py_INCREF(normname), normname);
    stack->name = (Py_INCREF(name), name);
    stack->next = *stack_;
    *stack_ = stack;

    return 0;
}

static void
tagstack_pop(tagstack **stack_)
{
    tagstack *tmp, *stack = *stack_;
    if (stack) {
        *stack_ = tmp = stack->next;
        Py_DECREF(stack->normname);
        Py_DECREF(stack->name);
        PyMem_Free(stack);
    }
}

/* ----------------------- END tagstack DEFINITION ----------------------- */

static int
lexer_error(tdi_soup_parser *self)
{
    switch (tdi_soup_lexer_error_get(self->lexer)) {
    case TDI_LEXER_ERR_ENV:
        break;

    case TDI_LEXER_ERR_EOF:
        self->last_error = TDI_PARSER_ERR_LEXER_EOF;
        break;

    case TDI_LEXER_ERR_FINAL:
        self->last_error = TDI_PARSER_ERR_LEXER_FINAL;
        break;
    }

    return -1;
}

static int
close_empty(tdi_soup_parser *self)
{
    PyObject *data, *name = self->tagstack->name;
    tdi_parser_event event;
    int res;

    if (!(data = PyString_FromString("")))
        return -1;
    Py_INCREF(name);

    self->inempty = 0;
    tagstack_pop(&self->tagstack);

    event.type = TDI_PARSER_EVENT_ENDTAG;
    event.info.endtag.name = name;
    event.info.endtag.data = data;
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(name);
    Py_DECREF(data);

    return res;
}

static int
handle_starttag(tdi_soup_parser *self, tdi_parser_event *event,
                tdi_lexer_event *event_)
{
    PyObject *name, *normname, *tmp, *data;
    int res;

    if (self->inempty && close_empty(self) == -1) return -1;

    /* sanitize */
    if (PyString_GET_SIZE(event_->info.starttag.name) == 0
        && PyList_GET_SIZE(event_->info.starttag.attr) == 0) {
        name = (Py_INCREF(self->lastopen), self->lastopen);
    }
    else {
        name = event_->info.starttag.name;
        Py_INCREF(name);
        Py_CLEAR(self->lastopen);
        self->lastopen = (Py_INCREF(name), name);
    }

    if (!(normname = self->normalize(self->normalize_ctx, name)))
        goto error;

    /* close unnestables */
    while (self->tagstack) {
        res = self->nestable(self->nestable_ctx,
                             self->tagstack->normname, normname);
        if (res == -1)
            goto error_normname;
        if (res) break;

        event->type = TDI_PARSER_EVENT_ENDTAG;
        if (!(data = PyString_FromString("")))
            goto error_normname;
        tmp = self->tagstack->name;
        event->info.endtag.name = (Py_INCREF(tmp), tmp);
        event->info.endtag.data = data;
        tagstack_pop(&self->tagstack);
        res = !self->cb(event, self->cb_ctx) ? 0 : -1;
        Py_DECREF(tmp);
        Py_DECREF(data);
        if (res == -1)
            goto error_normname;
    }

    /* CDATA */
    if (!event_->info.starttag.closed) {
        if ((res = self->cdata(self->cdata_ctx, normname)) == -1)
            goto error_normname;
        if (res) {
            res = tdi_soup_lexer_state_cdata(self->lexer, self->normalize,
                                             self->normalize_ctx, normname);
            if (res == -1) {
                lexer_error(self);
                goto error_normname;
            }
        }
    }

    /* pass event */
    event->type = TDI_PARSER_EVENT_STARTTAG;
    event->info.starttag.name = name;
    event->info.starttag.attr = event_->info.starttag.attr;
    event->info.starttag.closed = event_->info.starttag.closed;
    event->info.starttag.data = event_->info.starttag.data;
    if (self->cb(event, self->cb_ctx))
        goto error_normname;

    /* Maintain stack */
    if (!event_->info.starttag.closed) {
        if (tagstack_push(&self->tagstack, normname, name) == -1)
            goto error_normname;
        if ((res = self->empty(self->empty_ctx, normname)) == -1)
            goto error_normname;
        if (res)
            self->inempty = 1;
    }

    /* cleanup & finish */
    Py_DECREF(normname);
    Py_DECREF(name);
    return 0;

error_normname:
    Py_DECREF(normname);
error:
    Py_DECREF(name);

    if (!self->last_error)
        self->last_error = TDI_PARSER_ERR_ENV;
    return -1;
}

static int
handle_endtag(tdi_soup_parser *self, tdi_parser_event *event,
              tdi_lexer_event *event_)
{
    PyObject *normname, *name = event_->info.endtag.name;
    PyObject *toclose, *original, *data;
    tagstack *item;
    int cmp;

    if (!self->tagstack) {
        Py_INCREF(name);
    }
    else {
        if (PyString_GET_SIZE(name) == 0)
            name = self->tagstack->name;
        Py_INCREF(name);
        if (!(normname = self->normalize(self->normalize_ctx, name)))
            goto error;

        /* look if we're closing anything open.
         * This also resolves misnestings.
         */
        for (item = self->tagstack; item; item = item->next) {
            if (PyObject_Cmp(item->normname, normname, &cmp) == -1)
                goto error_normname;
            if (!cmp) break;
        }
        /* Found */
        if (item) {
            self->inempty = 0;
            while (self->tagstack) {
                toclose = self->tagstack->normname; Py_INCREF(toclose);
                original = self->tagstack->name; Py_INCREF(original);
                tagstack_pop(&self->tagstack);

                if (PyObject_Cmp(toclose, normname, &cmp) == -1)
                    goto error_loop;
                if (!cmp) {
                    Py_DECREF(original);
                    Py_DECREF(toclose);
                    break;
                }
                if (!(data = PyString_FromString("")))
                    goto error_loop;

                event->type = TDI_PARSER_EVENT_ENDTAG;
                event->info.endtag.name = original;
                event->info.endtag.data = data;
                if (self->cb(event, self->cb_ctx))
                    goto error_data;

                Py_DECREF(data);
                Py_DECREF(original);
                Py_DECREF(toclose);
            }
        }
        Py_DECREF(normname);
    }

    if (self->inempty && close_empty(self) == -1) goto error;

    event->type = TDI_PARSER_EVENT_ENDTAG;
    event->info.endtag.name = name;
    event->info.endtag.data = event_->info.endtag.data;
    if (self->cb(event, self->cb_ctx))
        goto error;

    Py_DECREF(name);
    return 0;

error_data:
    Py_DECREF(data);
error_loop:
    Py_DECREF(original);
    Py_DECREF(toclose);
error_normname:
    Py_DECREF(normname);
error:
    Py_DECREF(name);

    if (!self->last_error)
        self->last_error = TDI_PARSER_ERR_ENV;
    return -1;
}


static int
lexer_callback(tdi_lexer_event *event_, void *self_)
{
    tdi_soup_parser *self = self_;
    tdi_parser_event event;

    switch (event_->type) {
    case TDI_LEXER_EVENT_STARTTAG:
        return handle_starttag(self, &event, event_);

    case TDI_LEXER_EVENT_ENDTAG:
        return handle_endtag(self, &event, event_);

    case TDI_LEXER_EVENT_TEXT:
        if (self->inempty && close_empty(self) == -1) return -1;

        event.type = TDI_PARSER_EVENT_TEXT;
        event.info.text.data = event_->info.text.data;
        return !self->cb(&event, self->cb_ctx) ? 0 : -1;

    case TDI_LEXER_EVENT_COMMENT:
        if (self->inempty && close_empty(self) == -1) return -1;

        event.type = TDI_PARSER_EVENT_COMMENT;
        event.info.comment.data = event_->info.comment.data;
        return !self->cb(&event, self->cb_ctx) ? 0 : -1;

    case TDI_LEXER_EVENT_MSECTION:
        if (self->inempty && close_empty(self) == -1) return -1;

        event.type = TDI_PARSER_EVENT_MSECTION;
        event.info.msection.data = event_->info.msection.data;
        event.info.msection.name = event_->info.msection.name;
        event.info.msection.value = event_->info.msection.value;
        return !self->cb(&event, self->cb_ctx) ? 0 : -1;

    case TDI_LEXER_EVENT_DECL:
        if (self->inempty && close_empty(self) == -1) return -1;

        event.type = TDI_PARSER_EVENT_DECL;
        event.info.decl.data = event_->info.decl.data;
        event.info.decl.name = event_->info.decl.name;
        event.info.decl.value = event_->info.decl.value;
        return !self->cb(&event, self->cb_ctx) ? 0 : -1;

    case TDI_LEXER_EVENT_PI:
        if (self->inempty && close_empty(self) == -1) return -1;

        event.type = TDI_PARSER_EVENT_PI;
        event.info.pi.data = event_->info.pi.data;
        return !self->cb(&event, self->cb_ctx) ? 0 : -1;

    case TDI_LEXER_EVENT_ESCAPE:
        break;
    }

    /* Should not happen */
    PyErr_SetNone(PyExc_AssertionError);
    self->last_error = TDI_PARSER_ERR_ENV;
    return -1;
}

/* ------------------------------ BEGIN API ------------------------------ */

tdi_soup_parser *
tdi_soup_parser_new(tdi_parser_callback *cb, void *cb_ctx,
                    tdi_soup_parser_nestable_callback *nestable,
                    void *nestable_ctx,
                    tdi_soup_parser_cdata_callback *cdata,
                    void *cdata_ctx,
                    tdi_soup_parser_empty_callback *empty,
                    void *empty_ctx,
                    tdi_soup_parser_normalize_callback *normalize,
                    void *normalize_ctx)
{
    tdi_soup_parser *self;

    if (!(self = PyMem_Malloc(sizeof *self)))
        return NULL;

    if (!(self->lexer = tdi_soup_lexer_new(lexer_callback, self, 1)))
        goto error;
    if (!(self->lastopen = PyString_FromString("")))
        goto error_lexer;

    self->tagstack = NULL;
    self->inempty = 0;

    self->last_error = 0;
    self->cb = cb;
    self->cb_ctx = cb_ctx;
    self->nestable = nestable;
    self->nestable_ctx = nestable_ctx;
    self->cdata = cdata;
    self->cdata_ctx = cdata_ctx;
    self->empty = empty;
    self->empty_ctx = empty_ctx;
    self->normalize = normalize;
    self->normalize_ctx = normalize_ctx;

    return self;

error_lexer:
    TDI_SOUP_LEXER_CLEAR(self->lexer);
error:
    PyMem_Free(self);
    return NULL;
}

void
tdi_soup_parser_del(tdi_soup_parser *self)
{
    if (self) {
        TDI_SOUP_LEXER_CLEAR(self->lexer);
        Py_CLEAR(self->lastopen);
        while (self->tagstack)
            tagstack_pop(&self->tagstack);
        PyMem_Free(self);
    }
}

int
tdi_soup_parser_feed(tdi_soup_parser *self, PyObject *food)
{
    if (tdi_soup_lexer_feed(self->lexer, food) == -1)
        return lexer_error(self);

    return 0;
}

int
tdi_soup_parser_finalize(tdi_soup_parser *self)
{
    PyObject *data, *name;
    tdi_parser_event event;
    int res;

    if (tdi_soup_lexer_finalize(self->lexer) == -1)
        return lexer_error(self);

    while (self->tagstack) {
        if (!(data = PyString_FromString(""))) {
            self->last_error = TDI_PARSER_ERR_ENV;
            return -1;
        }
        name = self->tagstack->name;
        Py_INCREF(name);
        tagstack_pop(&self->tagstack);

        event.type = TDI_PARSER_EVENT_ENDTAG;
        event.info.endtag.name = name;
        event.info.endtag.data = data;
        res = self->cb(&event, self->cb_ctx);
        Py_DECREF(name);
        Py_DECREF(data);
        if (res) {
            self->last_error = TDI_PARSER_ERR_ENV;
            return -1;
        }
    }

    return 0;
}

const char *
tdi_soup_parser_lexer_state_get(tdi_soup_parser *self)
{
    return tdi_soup_lexer_state_get(self->lexer);
}

tdi_parser_error
tdi_soup_parser_error_get(tdi_soup_parser *self)
{
    return self->last_error;
}

/* ------------------------------- END API ------------------------------- */

