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

/* -------------------------- BEGIN DECLARATIONS ------------------------- */

#define FLAG_CONDITIONAL_IE_COMMENTS (1 << 0)

/* misusing flags as subsubstate info in decl lexer */
#define FLAG_DECL_DECL               (1 << 1)


typedef enum {
    STATE_FINAL,
    STATE_TEXT,
    STATE_CDATA,
    STATE_MARKUP,
    STATE_STARTTAG,
    STATE_ENDTAG,
    STATE_COMMENT,
    STATE_MSECTION,
    STATE_DECL,
    STATE_PI,
    STATE_EMPTY
} lexer_state;

typedef enum {
    STARTTAG_NAME,
    STARTTAG_ATTR,
    STARTTAG_ATTR_DQUOTE,
    STARTTAG_ATTR_SQUOTE,
    STARTTAG_FINAL
} starttag_substate;

typedef enum {
    COMMENT_INIT,
    COMMENT_IE,
    COMMENT_COMMENT
} comment_substate;

typedef enum {
    MSECTION_INIT,
    MSECTION_NAME_BEGIN,
    MSECTION_NAME_END,
    MSECTION_END,
    MSECTION_MSEND
} msection_substate;

typedef enum {
    DECL_INIT,
    DECL_NAME,
    DECL_VALUE_DULL,
    DECL_VALUE_QUOTE,
    DECL_VALUE_HYPHEN,
    DECL_VALUE_COMMENT,
    DECL_VALUE_LT,
    DECL_VALUE_MSECTION
} decl_substate;

struct tdi_soup_lexer {
    /* Last error, to be evaluated by the caller */
    tdi_lexer_error last_error;

    /* Event receiver */
    tdi_lexer_callback *cb;
    void *cb_ctx;

    /* cdata endtag stuff */
    tdi_soup_lexer_cdata_callback *normalize;
    void *normalize_ctx;
    PyObject *cdata_name;

    /* Current unevaluated buffer */
    PyObject *buffer;

    /* Current lexer state */
    lexer_state state;

    /* Buffer position already evaluated, used by some states */
    Py_ssize_t seen;

    /* Substate info used by some lexer states */
    Py_ssize_t pos1;
    Py_ssize_t pos2;
    int substate;

    /* Flag array */
    int flags;
};

/* --------------------------- END DECLARATIONS -------------------------- */

/*
 * Text lexer
 *
 * State: We are between tags or at the very beginning of the document
 * and look for a ``<``.
 */
static int
lex_TEXT(tdi_soup_lexer *self)
{
    const char *buf = PyString_AS_STRING(self->buffer);
    const char *sentinel = buf + PyString_GET_SIZE(self->buffer);
    const char *start = buf;
    PyObject *data, *tmp;
    tdi_lexer_event event;
    Py_ssize_t pos;
    int res;

    while (buf < sentinel) {
        if (*buf++ != '<') continue;

        /* Fast exit: no text to handle */
        if ((pos = --buf - start) == 0) {
            self->state = STATE_MARKUP;
            return 0;
        }

        /* Buffer split */
        if (!(data = PyString_FromStringAndSize(start, pos)))
            goto error;
        tmp = PyString_FromStringAndSize(buf, (Py_ssize_t)(sentinel - buf));
        if (!tmp)
            goto error_data;

        Py_CLEAR(self->buffer);
        self->buffer = tmp;
        event.info.text.data = data;
        self->state = STATE_MARKUP;
        goto handle;
    }

    /* The whole buffer is text */
    event.info.text.data = self->buffer;
    if (!(tmp = PyString_FromString("")))
        goto error;
    self->buffer = tmp;

handle:
    event.type = TDI_LEXER_EVENT_TEXT;
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(event.info.text.data);
    return res;

error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}


/*
 * (PR)CDATA lexer
 *
 * State: We are inside a text element and looking for the end tag only
 */
static int
lex_CDATA(tdi_soup_lexer *self)
{
    const char *buf, *start = PyString_AS_STRING(self->buffer);
    const char *sentinel = start + PyString_GET_SIZE(self->buffer);
    PyObject *data, *tmp;
    tdi_lexer_event event;
    Py_ssize_t pos;
    int res, incomplete = 0;

    buf = start;
    while (buf < sentinel) {
        if (*buf++ != '<') continue;
        if (!(buf < sentinel)) {
            if ((pos = --buf - start) > 0) {
                /* Pass seen text to the listener and wait for more input */
                if (!(data = PyString_FromStringAndSize(start, pos)))
                    goto error;
                tmp = PyString_FromStringAndSize(buf,
                                                (Py_ssize_t)(sentinel - buf));
                if (!tmp)
                    goto error_data;

                Py_CLEAR(self->buffer);
                self->buffer = tmp;
                event.info.text.data = data;
                incomplete = 1;
                goto handle;
            }
            return 1;
        }
        if (*buf != '/') continue;

        /* Fast exit: no text to handle */
        if ((pos = --buf - start) == 0) {
            self->seen = 2;
            self->state = STATE_ENDTAG;
            return 0;
        }

        /* Buffer split */
        if (!(data = PyString_FromStringAndSize(start, pos)))
            goto error;
        tmp = PyString_FromStringAndSize(buf, (Py_ssize_t)(sentinel - buf));
        if (!tmp)
            goto error_data;

        Py_CLEAR(self->buffer);
        self->buffer = tmp;
        event.info.text.data = data;
        self->seen = 2;
        self->state = STATE_ENDTAG;
        goto handle;
    }

    /* The whole buffer is text */
    event.info.text.data = self->buffer;
    if (!(tmp = PyString_FromString("")))
        goto error;
    self->buffer = tmp;

handle:
    event.type = TDI_LEXER_EVENT_TEXT;
    res = !self->cb(&event, self->cb_ctx) ? incomplete : -1;
    Py_DECREF(event.info.text.data);
    return res;

error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}


/*
 * Markup lexer
 *
 * State: We've hit a ``<`` character and now find out, what it's
 * becoming
 */
static int
lex_MARKUP(tdi_soup_lexer *self)
{
    PyObject *data, *tmp;
    const char *buf;
    tdi_lexer_event event;
    Py_ssize_t length;
    unsigned char c;
    int res;

    if ((length = PyString_GET_SIZE(self->buffer)) < 2)
        return 1;

#define u(c) (unsigned char)(c)

    switch (c = (buf = PyString_AS_STRING(self->buffer))[1]) {
    case u('/'): self->seen = 2; self->state = STATE_ENDTAG; return 0;
    case u('!'):
        self->substate = DECL_INIT; self->state = STATE_DECL; return 0;
    case u('?'): self->seen = 2; self->state = STATE_PI; return 0;
    case u('>'): self->state = STATE_EMPTY; return 0;
    }
    if (   (c >= u('a') && c <= u('z'))
        || (c >= u('A') && c <= u('Z'))
        || (c >= u('0') && c <= u('9'))) {
        self->seen = 2;
        self->substate = STARTTAG_NAME;
        self->state = STATE_STARTTAG;
        return 0;
    }

#undef u

    /* Didn't recognize. Treat '<' as text */
    if (!(data = PyString_FromStringAndSize(buf, 1)))
        goto error;
    if (!(tmp = PyString_FromStringAndSize(buf + 1, length - 1)))
        goto error_data;

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    event.info.text.data = data;
    event.type = TDI_LEXER_EVENT_TEXT;
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(event.info.text.data);
    return res;

error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}


/*
 * Processing instruction lexer
 *
 * State: We've hit a ``<?`` and now peek inside
 */
static int
lex_PI(tdi_soup_lexer *self)
{
    const char *buf, *start = PyString_AS_STRING(self->buffer);
    const char *sentinel = start + PyString_GET_SIZE(self->buffer);
    PyObject *data, *tmp;
    tdi_lexer_event event;
    int res;

    buf = start + self->seen;
    while (buf < sentinel) {
        if (*buf++ != '?') continue;
        if (!(buf < sentinel)) {
            self->seen = buf - start - 1;
            return 1;
        }
        if (*buf != '>') continue;

        ++buf;
        goto handle;
    }

    /* Need more data */
    self->seen = buf - start;
    return 1;

handle:
    data = PyString_FromStringAndSize(start, (Py_ssize_t)(buf - start));
    if (!data)
        goto error;
    tmp = PyString_FromStringAndSize(buf, (Py_ssize_t)(sentinel - buf));
    if (!tmp)
        goto error_data;

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    event.info.pi.data = data;
    event.type = TDI_LEXER_EVENT_PI;
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(event.info.pi.data);
    return res;

error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}


/*
 * Empty tag lexer
 *
 * State: We've hit a ``<>``
 */
static int
lex_EMPTY(tdi_soup_lexer *self)
{
    const char *buf;
    PyObject *data, *tmp, *name, *attr;
    tdi_lexer_event event;
    Py_ssize_t length;
    int res;

    buf = PyString_AS_STRING(self->buffer);
    length = PyString_GET_SIZE(self->buffer);

    if (!(data = PyString_FromStringAndSize(buf, 2)))
        goto error;
    if (!(name = PyString_FromString("")))
        goto error_data;
    if (!(attr = PyList_New(0)))
        goto error_name;
    if (!(tmp = PyString_FromStringAndSize(buf + 2, length - 2)))
        goto error_attr;

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    event.info.starttag.data = data;
    event.info.starttag.name = name;
    event.info.starttag.attr = attr;
    event.info.starttag.closed = 0;
    event.type = TDI_LEXER_EVENT_STARTTAG;
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(event.info.starttag.attr);
    Py_DECREF(event.info.starttag.name);
    Py_DECREF(event.info.starttag.data);
    return res;

error_attr:
    Py_DECREF(attr);
error_name:
    Py_DECREF(name);
error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}


/*
 * Starttag lexer
 *
 * State: We've hit a ``<x`` and now look for the ``>``.
 */
static int
starttag_attr(const char *, const char *, PyObject **, int *);

static int
lex_STARTTAG(tdi_soup_lexer *self)
{
    const char *buf, *start = PyString_AS_STRING(self->buffer);
    const char *sentinel = start + PyString_GET_SIZE(self->buffer);
    PyObject *data, *tmp, *name, *attr;
    tdi_lexer_event event;
    int res, closed;
    char c;

    buf = start + self->seen;

    switch ((starttag_substate)self->substate) {
    case STARTTAG_NAME:
        while (buf < sentinel) {switch (*buf++) {
        case '>':
            self->pos1 = (buf - start - 1);
            self->substate = STARTTAG_FINAL;
            goto state_final;

        case ' ': case '\t': case '\r': case '\n': case '\f': case '/':
            self->pos1 = (--buf - start);
            self->substate = STARTTAG_ATTR;
            goto state_attr;

        default:
            continue;
        }}
        /* Need more data */
        self->seen = buf - start;
        return 1;

    state_attr:
    case STARTTAG_ATTR:
        while (buf < sentinel) {switch (*buf++) {
        case '>':
            self->substate = STARTTAG_FINAL;
            goto state_final;

        case '"':
            self->substate = STARTTAG_ATTR_DQUOTE;
            goto state_quote;

        case '\'':
            self->substate = STARTTAG_ATTR_SQUOTE;
            goto state_quote;

        default:
            continue;
        }}
        /* Need more data */
        self->seen = buf - start;
        return 1;

    state_quote:
    case STARTTAG_ATTR_DQUOTE:
    case STARTTAG_ATTR_SQUOTE:
        c = (self->substate == STARTTAG_ATTR_DQUOTE) ? '"' : '\'';
        while (buf < sentinel) {
            if (*buf++ != c) continue;

            self->substate = STARTTAG_ATTR;
            goto state_attr;
        }
        /* Need more data */
        self->seen = buf - start;
        return 1;

    case STARTTAG_FINAL:
        break;
    }

state_final:
    if (!(data = PyString_FromStringAndSize(start, buf - start)))
        goto error;
    if (!(name = PyString_FromStringAndSize(start + 1, self->pos1 - 1)))
        goto error_data;
    if (starttag_attr(start + self->pos1, buf, &attr, &closed) == -1)
        goto error_name;
    if (!(tmp = PyString_FromStringAndSize(buf, sentinel - buf)))
        goto error_attr;

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    event.info.starttag.data = data;
    event.info.starttag.name = name;
    event.info.starttag.attr = attr;
    event.info.starttag.closed = closed;
    event.type = TDI_LEXER_EVENT_STARTTAG;
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(event.info.starttag.attr);
    Py_DECREF(event.info.starttag.name);
    Py_DECREF(event.info.starttag.data);
    return res;

error_attr:
    Py_DECREF(attr);
error_name:
    Py_DECREF(name);
error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}

/* Collect starttag attributes */
static int
starttag_attr(const char *buf, const char *sentinel, PyObject **attr_,
              int *closed)
{
    PyObject *attr, *name = NULL, *value = NULL, *tmp;
    const char *p = NULL;
    int res;

    *closed = 0;
    if (!(attr = PyList_New(0)))
        return -1;

    if ((sentinel - buf) <= 1) {
        *attr_ = attr;
        return 0;
    }

    while (buf < sentinel) {
        /* skip space */
        while (buf < sentinel) {switch (*buf++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': continue;
        default: p = --buf; break;
        } break;}

        /* Select name */
        switch (*buf++) {
        case '/':
            if (!(name = PyString_FromStringAndSize(--buf, 1)))
                goto error;
            break;

        case ' ': case '\t': case '\r': case '\n': case '\f':
        case '=': case '>':
            if (!(name = PyString_FromStringAndSize(p, --buf - p)))
                goto error;
            break;

        default:
            while (buf < sentinel) {switch (*buf++) {
            case ' ': case '\t': case '\r': case '\n': case '\f':
            case '/': case '=': case '>':
                if (!(name = PyString_FromStringAndSize(p, --buf - p)))
                    goto error;
                break;

            default: continue;
            } break;}
        }

        /* skip space */
        while (buf < sentinel) {switch (*buf++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': continue;
        default: --buf; break;
        } break;}

        /* Select value */
        if (*buf++ == '=') {
            /* skip space */
            p = buf;
            while (buf < sentinel) {switch (*buf++) {
            case ' ': case '\t': case '\r': case '\n': case '\f': continue;
            default: --buf; break;
            } break;}

            /* Collect quoted */
            if (*buf == '"' || *buf == '\'') {
                p = buf++;
                while (*buf++ != *p);
                if (!(value = PyString_FromStringAndSize(p, buf - p)))
                    goto error_name;
            }
            /* Collect unquoted */
            else if (p == buf) {
                while (buf < sentinel) {switch (*buf++) {
                case ' ': case '\t': case '\r': case '\n': case '\f':
                case '/': case '>':
                    if (!(value = PyString_FromStringAndSize(p, --buf - p)))
                        goto error_name;
                    break;

                default:
                    continue;
                } break;}
            }
            /* Empty */
            else {
                if (!(value = PyString_FromString("")))
                    goto error_name;
            }
        }
        else {
            if (PyString_GET_SIZE(name) == 0) {
                Py_DECREF(name);
                continue;
            }
            else if (PyString_GET_SIZE(name) == 1
                && PyString_AS_STRING(name)[0] == '/') {
                *closed = 1;
                Py_DECREF(name);
                continue;
            }
            value = (Py_INCREF(Py_None), Py_None);
            --buf;
        }

        /* append (name, value) tuple */
        if (!(tmp = PyTuple_New(2)))
            goto error_value;
        PyTuple_SET_ITEM(tmp, 0, name);
        PyTuple_SET_ITEM(tmp, 1, value);
        res = PyList_Append(attr, tmp);
        Py_DECREF(tmp);
        if (res == -1)
            goto error;
    }

    *attr_ = attr;
    return 0;

error_value:
    Py_DECREF(value);
error_name:
    Py_DECREF(name);
error:
    Py_DECREF(attr);
    return -1;
}


/*
 * Endtag lexer
 *
 * State: We've hit a ``</``.
 */
static int
lex_ENDTAG(tdi_soup_lexer *self)
{
    const char *buf, *p, *p1, *start = PyString_AS_STRING(self->buffer);
    const char *sentinel = start + PyString_GET_SIZE(self->buffer);
    PyObject *data, *tmp, *name;
    tdi_lexer_event event;
    int res;

    buf = start + self->seen;
    while (buf < sentinel) {
        if (*buf++ == '>') goto handle;
    }
    /* Need more data */
    self->seen = buf - start;
    return 1;

handle:
    data = PyString_FromStringAndSize(start, (Py_ssize_t)(buf - start));
    if (!data)
        goto error;

    p = start + 2;
    p1 = buf - 1;
    while (p < buf) {switch (*p++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': continue;
        default: --p; break;
    } break;}
    while (p1 >= p) {switch (*--p1) {
        case ' ': case '\t': case '\r': case '\n': case '\f': continue;
        default: ++p1; break;
    } break;}

    if (!(name = PyString_FromStringAndSize(p, (Py_ssize_t)(p1 - p))))
        goto error_data;
    tmp = PyString_FromStringAndSize(buf, (Py_ssize_t)(sentinel - buf));
    if (!tmp)
        goto error_name;

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    if (self->cdata_name) {
        if (!(tmp = self->normalize(self->normalize_ctx, name)))
            goto error_name;
        res = strcmp(PyString_AS_STRING(tmp),
                     PyString_AS_STRING(self->cdata_name));
        Py_DECREF(tmp);
        if (res) {
            self->state = STATE_CDATA;
        }
        else {
            self->normalize = NULL;
            self->normalize_ctx = NULL;
            Py_CLEAR(self->cdata_name);
        }
    }
    if (self->state == STATE_TEXT) {
        event.info.endtag.data = data;
        event.info.endtag.name = name;
        event.type = TDI_LEXER_EVENT_ENDTAG;
    }
    else {
        event.info.text.data = data;
        event.type = TDI_LEXER_EVENT_TEXT;
    }
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(name);
    Py_DECREF(data);
    return res;

error_name:
    Py_DECREF(name);
error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}


/*
 * Comment lexer
 *
 * State: We've hit a ``<!--``.
 */
static int
lex_COMMENT(tdi_soup_lexer *self)
{
    const char *buf = NULL, *p, *start = PyString_AS_STRING(self->buffer);
    const char *sentinel = start + PyString_GET_SIZE(self->buffer);
    PyObject *data, *tmp;
    tdi_lexer_event event;
    int res, emit = 0; /* 0 == comment, else == text */
    char c;

    switch ((comment_substate)self->substate) {
    case COMMENT_INIT:
        if ((sentinel - start) < 7)
            return 1;

        if (!(self->flags & FLAG_CONDITIONAL_IE_COMMENTS)
            || start[4] != '[') {
            goto state_comment;
        }
        self->substate = COMMENT_IE;
        /* Fall through */

    case COMMENT_IE:
        buf = start + 5;
        while (buf < sentinel) {switch (*buf++) {
        case ' ': case '\t': case '\r': case '\n': case '\f': continue;

        case 'i': case 'I':
            if (!(buf < sentinel)) return 1;
            if ((c = *buf++) != 'f' && c != 'F') goto state_comment;
            break;

        case 'e': case 'E':
            if (!(buf < sentinel)) return 1;
            switch (*buf++) {
            case 'l': case 'L':
                if (!(buf < sentinel)) return 1;
                if ((c = *buf++) != 's' && c != 'S') goto state_comment;
                if (!(buf < sentinel)) return 1;
                if ((c = *buf++) != 'e' && c != 'E') goto state_comment;
                break;

            case 'n': case 'N':
                if (!(buf < sentinel)) return 1;
                if ((c = *buf++) != 'd' && c != 'D') goto state_comment;
                if (!(buf < sentinel)) return 1;
                if ((c = *buf++) != 'i' && c!= 'I') goto state_comment;
                if (!(buf < sentinel)) return 1;
                if ((c = *buf++) != 'f' && c != 'F') goto state_comment;
                break;

            default:
                goto state_comment;
            }
            break;

        default:
            goto state_comment;
        } break;}

        /* Match until the end */
        while (buf < sentinel && *buf++ != ']');
        if (!(buf < sentinel)) return 1;
        if (*buf++ != '>') goto state_comment;
        emit = 1;
        goto handle;

    state_comment:
        self->seen = 4;
        self->substate = COMMENT_COMMENT;
    case COMMENT_COMMENT:
        buf = start + self->seen;
        while (buf < sentinel) {
            if (*buf++ != '-') continue;
            if (!(buf < sentinel)) return 1;
            p = buf;
            if (*buf++ == '-') {
                while (buf < sentinel) {switch (*buf++) {
                case '>':
                    goto handle;

                case ' ': case '\t': case '\r': case '\n': case '\f':
                    continue;
                } break;}
                if (!(buf < sentinel)) return 1;
            }
            buf = p;
        }
        /* Need more data */
        self->seen = buf - start;
        return 1;
    }


handle:
    data = PyString_FromStringAndSize(start, (Py_ssize_t)(buf - start));
    if (!data)
        goto error;
    tmp = PyString_FromStringAndSize(buf, (Py_ssize_t)(sentinel - buf));
    if (!tmp)
        goto error_data;

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    if (emit == 0) {
        event.info.comment.data = data;
        event.type = TDI_LEXER_EVENT_COMMENT;
    }
    else {
        event.info.text.data = data;
        event.type = TDI_LEXER_EVENT_TEXT;
    }
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(data);
    return res;

error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}


/*
 * Marked section lexer
 *
 * State: We've hit a ``<![`` and now seek the end
 */
static int
check_msmsection(tdi_soup_lexer *);

static int
lex_MSECTION(tdi_soup_lexer *self)
{
    const char *buf, *p, *p1, *start = PyString_AS_STRING(self->buffer);
    const char *sentinel = start + PyString_GET_SIZE(self->buffer);
    PyObject *data, *tmp, *name = NULL, *value = NULL;
    tdi_lexer_event event;
    int res, emit = 0; /* 0 == msection, else == text */

    switch ((msection_substate)self->substate) {
    case MSECTION_INIT:
        self->seen = 3;
        self->substate = MSECTION_NAME_BEGIN;
        /* fall through */

    case MSECTION_NAME_BEGIN:
        buf = start + self->seen;
        while (buf < sentinel) {switch (*buf++) {
        case ' ': case '\t': case '\r': case '\n': case '\f':
            continue;

        case ']': case '[': case '>':
            emit = 1;
            goto handle;

        default:
            self->pos1 = buf - start - 1;
            self->substate = MSECTION_NAME_END;
            break;
        } break;}
        self->seen = buf - start;
        if (!(buf < sentinel)) {
            return 1;
        }
        /* Fall through */

    case MSECTION_NAME_END:
        buf = start + self->seen;
        while (buf < sentinel) {switch (*buf++) {
        case ' ': case '\t': case '\r': case '\n': case '\f':
        case ']': case '[': case '>':
            self->pos2 = --buf - start;
            self->substate = check_msmsection(self)
                ? MSECTION_MSEND : MSECTION_END;
            break;

        default:
            continue;
        } break;}
        self->seen = buf - start;
        if (!(buf < sentinel)) {
            return 1;
        }
        /* Fall through */

    case MSECTION_MSEND:
    case MSECTION_END:
        buf = start + self->seen;
        while (buf < sentinel) {
            if (*buf++ != ']') continue;
            if (!(buf < sentinel)) return 1;
            p = p1 = buf - 1;
            while (buf < sentinel) {switch (*buf++) {
            case ' ': case '\t': case '\r': case '\n': case '\f': continue;

            case '-':
                if (self->substate == MSECTION_MSEND) {
                    if (!(buf < sentinel)) return 1;
                    if (*buf++ != '-') {
                        p = --buf;
                        break;
                    }
                    continue;
                }

            case '>':
                if (self->substate == MSECTION_MSEND)
                    goto handle;

            default:
                p = --buf;
                break;
            } break;}
            if (!(buf < sentinel)) return 1;
            if (*buf++ != ']') {buf = p; break;}

            while (buf < sentinel) {switch (*buf++) {
            case ' ': case '\t': case '\r': case '\n': case '\f': continue;
            case '>':
                goto handle;
            default:
                p = --buf;
                break;
            } break;}
            if (!(buf < sentinel)) return 1;
        }
        self->seen = buf - start;
        return 1;
    }
    /* Cant happen */
    return 1;

handle:
    if (self->substate == MSECTION_MSEND)
        emit = 1;

    data = PyString_FromStringAndSize(start, (Py_ssize_t)(buf - start));
    if (!data)
        goto error;
    tmp = PyString_FromStringAndSize(buf, (Py_ssize_t)(sentinel - buf));
    if (!tmp)
        goto error_data;
    if (emit == 0) {
        name = PyString_FromStringAndSize(start + self->pos1,
                                          self->pos2 - self->pos1);
        if (!name)
            goto error_tmp;

        p = start + self->pos2;
        while (p < p1 && *p++ != '[');
        if (!(p < p1)) p = start + self->pos2;
        if (!(value = PyString_FromStringAndSize(p, p1 - p))) {
            Py_DECREF(name);
            goto error_tmp;
        }
    }

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    if (emit == 0) {
        event.info.msection.value = value;
        event.info.msection.name = name;
        event.info.msection.data = data;
        event.type = TDI_LEXER_EVENT_MSECTION;
    }
    else {
        event.info.text.data = data;
        event.type = TDI_LEXER_EVENT_TEXT;
    }
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    if (emit == 0) {
        Py_DECREF(value);
        Py_DECREF(name);
    }
    Py_DECREF(data);
    return res;

error_tmp:
    Py_DECREF(tmp);
error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;
}

static int
check_msmsection(tdi_soup_lexer *self)
{
    const char *buf = PyString_AS_STRING(self->buffer) + self->pos1;
    Py_ssize_t length = self->pos2 - self->pos1;

    if (self->flags & FLAG_CONDITIONAL_IE_COMMENTS) {switch (length) {
    case 2:
        switch (*buf++) {
        case 'i': case 'I': switch (*buf) {
        case 'f': case 'F': return 1;
        }}
        break;

    case 4:
        switch (*buf++) {
        case 'e': case 'E': switch (*buf++) {
        case 'l': case 'L': switch (*buf++) {
        case 's': case 'S': switch (*buf) {
        case 'e': case 'E': return 1;
        }}}}
        break;

    case 5:
        switch (*buf++) {
        case 'e': case 'E': switch (*buf++) {
        case 'n': case 'N': switch (*buf++) {
        case 'd': case 'D': switch (*buf++) {
        case 'i': case 'I': switch (*buf) {
        case 'f': case 'F': return 1;
        }}}}}
        break;
    }}

    return 0;
}


/*
 * Declaration lexer
 *
 * State: We've hit a ``<!`` and now peek inside
 */
static int
lex_DECL(tdi_soup_lexer *self)
{
    PyObject *data, *tmp, *name, *value;
    const char *buf, *p, *p1, *start = PyString_AS_STRING(self->buffer);
    const char *sentinel = start + PyString_GET_SIZE(self->buffer);
    tdi_lexer_event event;
    int res;
    char c;

    switch ((decl_substate)self->substate) {
    case DECL_INIT:
        if ((sentinel - start) < 3)
            return 1;

        self->flags &= ~FLAG_DECL_DECL;

        switch (*(buf = start + 2)) {
        case '-':
            if (!(++buf < sentinel))
                return 1;
            if (*buf == '-') {
                self->substate = COMMENT_INIT;
                self->state = STATE_COMMENT;
                return 0;
            }
            break;

        case '[':
            self->substate = MSECTION_INIT;
            self->state = STATE_MSECTION;
            return 0;
        }
        self->seen = 2;
        self->substate = DECL_NAME;
        /* fall through */

    case DECL_NAME:
        buf = start + self->seen;
        while (buf < sentinel) {switch (*buf++) {
        case ' ': case '\t': case '\r': case '\n': case '\f':
        case ']': case '[': case '>':
            self->pos1 = --buf - start;
            self->substate = DECL_VALUE_DULL;
            break;

        default:
            continue;
        } break;}
        self->seen = buf - start;
        if (!(buf < sentinel)) return 1;
        /* Fall through */

    state_value_dull:
        self->substate = DECL_VALUE_DULL;
    case DECL_VALUE_DULL:
        buf = start + self->seen;
        while (buf < sentinel) {switch (*buf++) {
        case '"':
        case '\'':
            self->pos2 = (self->seen = buf - start) - 1;
            goto state_value_quote;

        case '-':
            self->seen = buf - start; goto state_value_hyphen;

        case '<':
            if (self->flags & FLAG_DECL_DECL) continue;
            self->seen = buf - start; goto state_value_lt;

        case '>':
            if (self->flags & FLAG_DECL_DECL)
                self->flags &= ~FLAG_DECL_DECL;
            else
                goto handle;

        default:
            continue;
        }}
        self->seen = buf - start;
        return 1;

    state_value_quote:
        self->substate = DECL_VALUE_QUOTE;
    case DECL_VALUE_QUOTE:
        buf = start + self->seen;
        c = start[self->pos2];
        while (buf < sentinel && *buf++ != c);
        if (!(buf < sentinel)) return 1;
        self->seen = buf - start;
        goto state_value_dull;

    state_value_hyphen:
        self->substate = DECL_VALUE_HYPHEN;
    case DECL_VALUE_HYPHEN:
        buf = start + self->seen;
        if (!(buf < sentinel)) return 1;
        if (*buf != '-') goto state_value_dull;
        self->seen = ++buf - start;
        self->substate = DECL_VALUE_COMMENT;
        /* Fall through */

    case DECL_VALUE_COMMENT:
        buf = start + self->seen;
        while (buf < sentinel) {
            if (*buf++ != '-') continue;
            if (!(buf < sentinel)) {--buf; break;}
            if (*buf++ != '-') break;
            self->seen = buf - start;
            goto state_value_dull;
        }
        self->seen = buf - start;
        return 1;

    state_value_lt:
        self->substate = DECL_VALUE_LT;
    case DECL_VALUE_LT:
        buf = start + self->seen;
        if (!(buf < sentinel)) return 1;
        if (*buf == '!') {
            if (!(++buf < sentinel)) return 1;
            if (*buf == '[') {
                self->seen = buf - start + 1;
                goto state_value_msection;
            }
        }
        self->seen = buf - start;
        self->flags |= FLAG_DECL_DECL;
        goto state_value_dull;

    state_value_msection:
        self->substate = DECL_VALUE_MSECTION;
    case DECL_VALUE_MSECTION:
        buf = start + self->seen;
        while (buf < sentinel) {
            if (*buf++ != ']') continue;
            p = buf;
            while (buf < sentinel) {switch (*buf++) {
            case ' ': case '\t': case '\r': case '\n': case '\f': continue;

            case ']':
                while (buf < sentinel) {switch (*buf++) {
                case ' ': case '\t': case '\r': case '\n': case '\f':
                    continue;

                case '>':
                    self->seen = buf - start;
                    goto state_value_dull;
                } break;}

            default:
                buf = p;
                break;
            } break;}
        }
        /* don't set self->seen; need to rematch from the beginning */
        return 1;
    }
    /* Cant happen */
    return 1;

handle:
    data = PyString_FromStringAndSize(start, (Py_ssize_t)(buf - start));
    if (!data)
        goto error;
    if (!(name = PyString_FromStringAndSize(start + 2, self->pos1 - 2)))
        goto error_data;

    p = buf - 1;
    p1 = start + self->pos1;
    /* trim spaces */
    while (p > p1) {switch (*--p) {
    case ' ': case '\t': case '\r': case '\n': case '\f': continue;
    default: ++p; break;
    } break;}
    while (p1 < p) {switch (*p1++) {
    case ' ': case '\t': case '\r': case '\n': case '\f': continue;
    default: --p1; break;
    } break;}
    value = PyString_FromStringAndSize(p1, p - p1);
    if (!value)
        goto error_name;

    tmp = PyString_FromStringAndSize(buf, (Py_ssize_t)(sentinel - buf));
    if (!tmp)
        goto error_value;

    Py_CLEAR(self->buffer);
    self->buffer = tmp;
    self->state = STATE_TEXT;

    event.info.decl.value = value;
    event.info.decl.name = name;
    event.info.decl.data = data;
    event.type = TDI_LEXER_EVENT_DECL;
    res = !self->cb(&event, self->cb_ctx) ? 0 : -1;
    Py_DECREF(value);
    Py_DECREF(name);
    Py_DECREF(data);
    return res;

error_value:
    Py_DECREF(value);
error_name:
    Py_DECREF(name);
error_data:
    Py_DECREF(data);
error:
    self->last_error = TDI_LEXER_ERR_ENV;
    return -1;

}


/*
 * Main lexer loop, dispatches to actual lexer functions.
 */

#define LEX(what) \
    case STATE_##what: switch (lex_##what(self)) { \
    case -1: return -1; \
    case 0: continue; \
    default: return 0; \
    }

static int
dispatch_loop(tdi_soup_lexer *self)
{
    while (PyString_GET_SIZE(self->buffer) > 0) {
        switch (self->state) {
        LEX(TEXT)
        LEX(MARKUP)
        LEX(CDATA)
        LEX(PI)
        LEX(EMPTY)
        LEX(STARTTAG)
        LEX(ENDTAG)
        LEX(DECL)
        LEX(COMMENT)
        LEX(MSECTION)

        case STATE_FINAL:
            self->last_error = TDI_LEXER_ERR_FINAL;
            return -1;
        }
    }
    return 0;
}
#undef LEX

/* ------------------------------ BEGIN API ------------------------------ */

tdi_soup_lexer *
tdi_soup_lexer_new(tdi_lexer_callback *cb, void *cb_ctx,
                   int conditional_ie_comments)
{
    tdi_soup_lexer *self;

    if (!(self = PyMem_Malloc(sizeof *self)))
        return NULL;

    if (!(self->buffer = PyString_FromString(""))) {
        PyMem_Free(self);
        return NULL;
    }
    self->last_error = 0;
    self->cb = cb;
    self->cb_ctx = cb_ctx;
    self->normalize = NULL;
    self->normalize_ctx = NULL;
    self->cdata_name = NULL;
    self->state = STATE_TEXT;
    self->flags = 0;
    if (conditional_ie_comments)
        self->flags |= FLAG_CONDITIONAL_IE_COMMENTS;

    return self;
}

void
tdi_soup_lexer_del(tdi_soup_lexer *self)
{
    if (self) {
        Py_CLEAR(self->buffer);
        Py_CLEAR(self->cdata_name);
        PyMem_Free(self);
    }
}

int
tdi_soup_lexer_feed(tdi_soup_lexer *self, PyObject *food)
{
    PyString_Concat(&self->buffer, food);
    if (!self->buffer) {
        self->last_error = TDI_LEXER_ERR_ENV;
        return -1;
    }

    return dispatch_loop(self);
}

int
tdi_soup_lexer_finalize(tdi_soup_lexer *self)
{
    if (dispatch_loop(self) == -1)
        return -1;

    if (PyString_GET_SIZE(self->buffer) != 0) {
        self->last_error = TDI_LEXER_ERR_EOF;
        return -1;
    }

    self->state = STATE_FINAL;
    return 0;
}

const char *
tdi_soup_lexer_state_get(tdi_soup_lexer *self)
{
    switch (self->state)
    {
    case STATE_FINAL:    return "FINAL";
    case STATE_TEXT:     return "TEXT";
    case STATE_CDATA:    return "CDATA";
    case STATE_MARKUP:   return "MARKUP";
    case STATE_STARTTAG: return "STARTTAG";
    case STATE_ENDTAG:   return "ENDTAG";
    case STATE_COMMENT:  return "COMMENT";
    case STATE_MSECTION: return "MSECTION";
    case STATE_DECL:     return "DECL";
    case STATE_PI:       return "PI";
    case STATE_EMPTY:    return "EMPTY";
    }

    /* should not happen(tm) */
    return "unknown";
}

int
tdi_soup_lexer_state_cdata(tdi_soup_lexer *self,
                           tdi_soup_lexer_cdata_callback *cb,
                           void *cb_ctx, PyObject *name)
{
    if (self->state != STATE_FINAL) {
        self->state = STATE_CDATA;
        self->normalize = cb;
        self->normalize_ctx = cb_ctx;
        if (!(self->cdata_name = cb(cb_ctx, name))) {
            self->last_error = TDI_LEXER_ERR_ENV;
            return -1;
        }
    }

    return 0;
}

tdi_lexer_error
tdi_soup_lexer_error_get(tdi_soup_lexer *self)
{
    return self->last_error;
}

/* ------------------------------- END API ------------------------------- */

