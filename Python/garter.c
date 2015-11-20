/* -*- c-basic-offset: 4 -*- */
#include "Python.h"
#include "Python-ast.h"
#include "garter.h"

/* The rest of python just uses int as a boolean type */
/* This communicates intent better in my opinion */
typedef int GBoolean;
#define GTrue 1
#define GFalse 0

/*
  GarterType
*/

typedef enum _GarterTypeKind {
    GT_INT,
    GT_FLOAT,
    GT_BOOL,
    GT_STR,
    GT_DICT,
    GT_LIST,
    GT_CLASS
} GarterTypeKind;

typedef struct _GarterType
{
    PyObject_HEAD

    GarterTypeKind kind;

    /*
      Additional type information
      CLASS: property_name => Type
      LIST: Type
      DICT: tuple (Type, Type)
      TYPE: Type
    */
    PyObject *meta;
} GarterType;

static void
GarterType_dealloc(GarterType* type)
{
    Py_XDECREF(type->meta);
}

PyTypeObject GarterType_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "gartertype",                       /* tp_name */
    sizeof(GarterType),                 /* tp_basicsize */
    0,                                  /* tp_itemsize */
    /* methods */
    (destructor)GarterType_dealloc,     /* tp_dealloc */
    0,                                  /* tp_print */
    0,                                  /* tp_getattr */
    0,                                  /* tp_setattr */
    0,                                  /* tp_reserved */
    0,                                  /* tp_repr */
    0,                                  /* tp_as_number */
    0,                                  /* tp_as_sequence */
    0,                                  /* tp_as_mapping */
    0,                                  /* tp_hash */
    0,                                  /* tp_call */
    0,                                  /* tp_str */
    PyObject_GenericGetAttr,            /* tp_getattro */
    0,                                  /* tp_setattro */
    0,                                  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                 /* tp_flags */
    0,                                  /* tp_doc */
    0,                                  /* tp_traverse */
    0,                                  /* tp_clear */
    0,                                  /* tp_richcompare */
    0,                                  /* tp_weaklistoffset */
    0,                                  /* tp_iter */
    0,                                  /* tp_iternext */
    0,                                  /* tp_methods */
    0,                                  /* tp_members */
    0,                                  /* tp_getset */
    0,                                  /* tp_base */
    0,                                  /* tp_dict */
    0,                                  /* tp_descr_get */
    0,                                  /* tp_descr_set */
    0,                                  /* tp_dictoffset */
    0,                                  /* tp_init */
    PyType_GenericAlloc,                /* tp_alloc */
    0,                                  /* tp_new */
    PyObject_Free,                      /* tp_free */
};

static PyObject * /* owned */
GarterType_New(GarterTypeKind kind, PyObject *meta)
{
    GarterType *o = PyObject_New(GarterType, &GarterType_Type);
    o->kind = kind;
    o->meta = meta;
    Py_XINCREF(meta);
    return (PyObject *)o;
}

static int
GarterType_Check(PyObject *obj)
{
    assert((void *) &((GarterType *) obj)->ob_base == (void *) obj);
    return Py_TYPE(obj) == &GarterType_Type;
}

static GarterTypeKind
GarterType_Kind(PyObject *obj)
{
    assert(GarterType_Check(obj));
    return ((GarterType *)obj)->kind;
}

static PyObject *
GarterType_Meta(PyObject *obj)
{
    assert(GarterType_Check(obj));
    return ((GarterType *)obj)->meta;
}

static GBoolean
GarterType_IsComplete(PyObject *obj)
{
    if (!obj)
        return GFalse;

    PyObject *meta = GarterType_Meta(obj);
    switch (GarterType_Kind(obj)) {
    case GT_LIST: {
        return GarterType_IsComplete(meta);
    }
    case GT_DICT: {
        if (!meta)
            return GFalse;
        assert(PyTuple_Check(meta));
        return GarterType_IsComplete(PyTuple_GetItem(meta, 0)) &&
            GarterType_IsComplete(PyTuple_GetItem(meta, 1));
    }
    case GT_CLASS: {
        if (!meta)
            return GFalse;
        return GTrue;
    }
    default:
        return GTrue;
    }
}

static void
GarterType_LateBindMeta(PyObject *obj, PyObject *meta)
{
    assert(!GarterType_Meta(obj) && meta);
    Py_INCREF(meta);
    ((GarterType *)obj)->meta = meta;
}

/* NOTE: This will late bind if required to ensure equality */
static GBoolean
GarterType_Equal(PyObject *a, PyObject *b)
{
    assert(GarterType_Check(a) && GarterType_Check(b));
    if (a == b) {
        return GTrue;
    }

    if (GarterType_Kind(a) != GarterType_Kind(b)) {
        return GFalse;
    }

    PyObject *aMeta = GarterType_Meta(a);
    PyObject *bMeta = GarterType_Meta(b);
    switch (GarterType_Kind(a)) {
    case GT_DICT: {
        if (!aMeta && !bMeta) { /* empty dictionaries */
            return GTrue;
        } else if (!aMeta) {
            GarterType_LateBindMeta(a, bMeta);
            return GTrue;
        } else if (!bMeta) {
            GarterType_LateBindMeta(b, aMeta);
            return GTrue;
        } else {
            assert(PyTuple_Check(aMeta) && PyTuple_Check(bMeta));
            GBoolean keys_match = GarterType_Equal(PyTuple_GetItem(aMeta, 0),
                                                   PyTuple_GetItem(bMeta, 0));
            GBoolean vals_match = GarterType_Equal(PyTuple_GetItem(aMeta, 1),
                                                   PyTuple_GetItem(bMeta, 1));
            return keys_match && vals_match;
        }
    }
    case GT_LIST: {
        if (!aMeta && !bMeta) { /* Empty lists */
            return GTrue;
        } else if (!aMeta) {
            GarterType_LateBindMeta(a, bMeta);
            return GTrue;
        } else if (!bMeta) {
            GarterType_LateBindMeta(b, aMeta);
            return GTrue;
        } else {
            assert(GarterType_Check(aMeta) && GarterType_Check(bMeta));
            return GarterType_Equal(aMeta, bMeta);
        }
    }
    case GT_CLASS: {
        /* XXX: Late binding for classes (None object) */
        /* Meta objects define the class - they are unique per-class */
        return aMeta == bMeta;
    }
    default: {
        return GTrue;
    }
    }
}

/*
  Primitive Types
*/

static GarterType _GarterType_INT = {
    PyObject_HEAD_INIT(&GarterType_Type)
    GT_INT, NULL
};
static PyObject *GarterType_INT = (PyObject *) &_GarterType_INT;

static GarterType _GarterType_FLOAT = {
    PyObject_HEAD_INIT(&GarterType_Type)
    GT_FLOAT, NULL
};
static PyObject *GarterType_FLOAT = (PyObject *) &_GarterType_FLOAT;

static GarterType _GarterType_BOOL= {
    PyObject_HEAD_INIT(&GarterType_Type)
    GT_BOOL, NULL
};
static PyObject *GarterType_BOOL = (PyObject *) &_GarterType_BOOL;

static GarterType _GarterType_STR = {
    PyObject_HEAD_INIT(&GarterType_Type)
    GT_STR, NULL
};
static PyObject *GarterType_STR = (PyObject *) &_GarterType_STR;

/*
  GarterScope
*/

typedef struct _GarterScope
{
    PyObject_HEAD

    PyObject *up; /* GarterScope */
    PyObject *items; /* Dict{String => GarterType} */

    /* Only used at global scope */
    PyObject *filename; /* String */
} GarterScope;

static void
GarterScope_dealloc(GarterScope *scope)
{
    Py_XDECREF(scope->up);
    Py_XDECREF(scope->items);
    Py_XDECREF(scope->filename);
}

PyTypeObject GarterScope_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "garterscope",                      /* tp_name */
    sizeof(GarterScope),                /* tp_basicsize */
    0,                                  /* tp_itemsize */
    /* methods */
    (destructor)GarterScope_dealloc,    /* tp_dealloc */
    0,                                  /* tp_print */
    0,                                  /* tp_getattr */
    0,                                  /* tp_setattr */
    0,                                  /* tp_reserved */
    0,                                  /* tp_repr */
    0,                                  /* tp_as_number */
    0,                                  /* tp_as_sequence */
    0,                                  /* tp_as_mapping */
    0,                                  /* tp_hash */
    0,                                  /* tp_call */
    0,                                  /* tp_str */
    PyObject_GenericGetAttr,            /* tp_getattro */
    0,                                  /* tp_setattro */
    0,                                  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                 /* tp_flags */
    0,                                  /* tp_doc */
    0,                                  /* tp_traverse */
    0,                                  /* tp_clear */
    0,                                  /* tp_richcompare */
    0,                                  /* tp_weaklistoffset */
    0,                                  /* tp_iter */
    0,                                  /* tp_iternext */
    0,                                  /* tp_methods */
    0,                                  /* tp_members */
    0,                                  /* tp_getset */
    0,                                  /* tp_base */
    0,                                  /* tp_dict */
    0,                                  /* tp_descr_get */
    0,                                  /* tp_descr_set */
    0,                                  /* tp_dictoffset */
    0,                                  /* tp_init */
    PyType_GenericAlloc,                /* tp_alloc */
    0,                                  /* tp_new */
    PyObject_Free,                      /* tp_free */
};

static int
GarterScope_Check(PyObject *obj)
{
    assert((void *) &((GarterType *) obj)->ob_base == (void *) obj);
    return Py_TYPE(obj) == &GarterScope_Type;
}

static PyObject * /* owned */
GarterScope_New(PyObject *up)
{
    assert(!up || GarterScope_Check(up));
    GarterScope *o = PyObject_New(GarterScope, &GarterScope_Type);
    if (!o)
        return NULL;

    o->up = up;
    Py_XINCREF(up);

    PyObject *items = PyDict_New();
    if (!items) {
        Py_DECREF(o);
        return NULL;
    }
    o->items = items;
    o->filename = NULL;

    return (PyObject *)o;
}

static PyObject *
GarterScope_Up(PyObject *obj)
{
    assert(GarterScope_Check(obj));
    return ((GarterScope *)obj)->up;
}

static PyObject *
GarterScope_Items(PyObject *obj)
{
    assert(GarterScope_Check(obj));
    return ((GarterScope *)obj)->items;
}

static PyObject *
GarterScope_Global(PyObject *obj)
{
    while (GarterScope_Up(obj)) {
        obj = GarterScope_Up(obj);
    }
    return obj;
}

static PyObject *
GarterScope_FileName(PyObject *obj)
{
    PyObject *global = GarterScope_Global(obj);

    return ((GarterScope *)global)->filename;
}

static void
_GarterScope_Error(PyObject *scope,
                   int lineno,
                   int col_offset,
                   PyObject *errmsg)
{
    PyObject *value, *loc, *tmp, *filename;
    filename = GarterScope_FileName(scope);

    loc = PyErr_ProgramTextObject(filename, lineno);
    if (!loc) {
        Py_INCREF(Py_None);
        loc = Py_None;
    }
    tmp = Py_BuildValue("(OiiN)", filename, lineno, col_offset, loc);
    if (!tmp)
        return;
    value = PyTuple_Pack(2, errmsg, tmp);
    Py_DECREF(tmp);
    if (value) {
        PyErr_SetObject(PyExc_SyntaxError, value);
        Py_DECREF(value);
    }
}

#define Garter_ERROR(NODE, ...)                                    \
    do {                                                           \
        PyObject *__vf_errmsg = PyUnicode_FromFormat(__VA_ARGS__); \
        _GarterScope_Error(scope,                                  \
                           NODE->lineno, NODE->col_offset,         \
                           __vf_errmsg);                           \
        Py_DECREF(__vf_errmsg);                                    \
        goto fail; /* functions must define fail label */          \
    } while (0)

#define UNIMPLEMENTED(NODE) Garter_ERROR(NODE,                  \
                                         "UNIMPLEMENTED %s:%d", \
                                         __FILE__, __LINE__);

static PyObject *
GarterScope_ValidationBegin(PyObject *obj, PyObject *filename)
{
    assert(GarterScope_Check(obj) &&
           !GarterScope_Up(obj) &&
           !GarterScope_FileName(obj));

    ((GarterScope *)obj)->filename = filename;
    Py_INCREF(filename);

    /*
      We return a copy of the items array as a back up to be passed
      to GarterScope_ValidationFail() if something goes wrong, such
      that an invalid global scope isn't maintained between interpereter
      lines of execution
    */
    PyObject *items = GarterScope_Items(obj);
    assert(PyDict_Check(items));
    return PyDict_Copy(items);
}

static void
GarterScope_ValidationOk(PyObject *obj)
{
    assert(GarterScope_Check(obj) &&
           !GarterScope_Up(obj) &&
           GarterScope_FileName(obj));
    GarterScope *o = (GarterScope *)obj;
    Py_DECREF(o->filename);
    o->filename = NULL;
}

static void
GarterScope_ValidationFail(PyObject *obj, PyObject *backup)
{
    assert(PyDict_Check(backup));
    GarterScope_ValidationOk(obj);
    GarterScope *o = (GarterScope *)obj;
    Py_DECREF(o->items);
    o->items = backup;
    Py_INCREF(backup);
}

/*
  Main validation logic
*/

/* FORWARD */
static PyObject *validate_type(PyObject *scope, expr_ty expr);
static PyObject *validate_expr(PyObject *scope, expr_ty expr, GBoolean lvalue);
static PyObject *validate_binop_expr(PyObject *scope, expr_ty expr);
static PyObject *validate_unaryop_expr(PyObject *scope, expr_ty expr);

static GBoolean validate_decl_target(PyObject *scope,
                                  expr_ty expr,
                                  PyObject *type);
static GBoolean validate_assign_stmt(PyObject *scope, stmt_ty stmt,
                                     GBoolean sroot);
static GBoolean validate_stmts(PyObject *scope, asdl_seq *seq, GBoolean sroot);
static GBoolean validate_stmt(PyObject *scope, stmt_ty stmt, GBoolean sroot);
static GBoolean validate_mod(PyObject *scope, mod_ty mod);

#define INCREF_RET_FINALLY(TYPE) \
    do {                         \
        Py_XDECREF(ret);         \
        ret = TYPE;              \
        Py_XINCREF(ret);         \
        goto finally;            \
    } while (0)

#define RET_FINALLY(TYPE) \
    do {                  \
        ret = TYPE;       \
        goto finally;     \
    } while (0)

static GBoolean
validate_decl_target(PyObject *scope, expr_ty expr, PyObject *type)
{
    assert(expr && type);

    switch (expr->kind) {
    case Name_kind: {
        identifier name = expr->v.Name.id;
        assert(PyUnicode_Check(name));

        PyObject *items = GarterScope_Items(scope);
        assert(PyDict_Check(items));

        switch (PyDict_Contains(items, name)) {
        case -1: return GFalse;
        case 0: break;
        default:
            Garter_ERROR(expr,
                         "Variable with name %V has already been defined",
                         name);
        }

        if (PyDict_SetItem(items, name, type) == -1) {
            return GFalse;
        }

        return GTrue;
    }
    default: {
        Garter_ERROR(expr,
                     "Complex expressions are not legal on the left hand side "
                     "of a variable declaration");
    }
    }

fail:
    return GFalse;
}

static PyObject * /* owned */
validate_type(PyObject *scope, expr_ty expr)
{
    assert(expr);

    PyObject *ret = NULL;
    PyObject *key_type = NULL, *value_type = NULL;

    switch (expr->kind) {
    case Name_kind: {
        identifier name = expr->v.Name.id;
        assert(PyUnicode_Check(name));
        PyUnicode_READY(name);

        /* XXX: Also handle class types */
        if (PyUnicode_CompareWithASCIIString(name, "int") == 0) {
            Py_INCREF(GarterType_INT);
            return GarterType_INT;
        } else if (PyUnicode_CompareWithASCIIString(name, "float") == 0) {
            Py_INCREF(GarterType_FLOAT);
            return GarterType_FLOAT;
        } else if (PyUnicode_CompareWithASCIIString(name, "str") == 0) {
            Py_INCREF(GarterType_STR);
            return GarterType_STR;
        } else if (PyUnicode_CompareWithASCIIString(name, "bool") == 0) {
            Py_INCREF(GarterType_BOOL);
            return GarterType_BOOL;
        } else {
            Garter_ERROR(expr, "Unrecognized type name %V", name);
        }
    }
    case Dict_kind: {
        asdl_seq *keys = expr->v.Dict.keys;
        asdl_seq *values = expr->v.Dict.values;

        if (asdl_seq_LEN(keys) != 1 ||
            asdl_seq_LEN(values) != 1) {
            Garter_ERROR(expr,
                         "Dictionary types may only have one key-value "
                         "type-pair");
        }

        expr_ty key = (expr_ty) asdl_seq_GET(keys, 0);
        expr_ty value = (expr_ty) asdl_seq_GET(values, 0);
        if (!key || !value) {
            PyErr_SetString(PyExc_ValueError, "None disallowed as a type");
            goto fail;
        }

        key_type = validate_type(scope, key);
        if (!key_type)
            goto fail;

        value_type = validate_type(scope, value);
        if (!value_type)
            goto fail;

        PyObject *meta = PyTuple_Pack(2, key_type, value_type);
        if (!meta)
            goto fail;

        ret = GarterType_New(GT_DICT, meta);
        Py_XDECREF(meta);
        goto finally;
    }
    case List_kind: {
        asdl_seq *elts = expr->v.List.elts;

        if (asdl_seq_LEN(elts) != 1) {
            Garter_ERROR(expr,
                         "List type literals may only have a single item");
        }

        expr_ty elt = (expr_ty) asdl_seq_GET(elts, 0);
        if (!elt) {
            PyErr_SetString(PyExc_ValueError, "None disallowed as a type");
            goto fail;
        }

        PyObject *meta = validate_type(scope, elt);
        if (!meta)
            goto fail;

        ret = GarterType_New(GT_LIST, meta);
        Py_XDECREF(meta);
        goto finally;
    }
    default:
        Garter_ERROR(expr, "Illegal type form");
    }

    Garter_ERROR(expr, "Unimplemented validate_type");

fail:
    ret = NULL;
finally:
    Py_XDECREF(key_type);
    Py_XDECREF(value_type);
    return ret;
}
static PyObject * /* owned */
validate_if_expr(PyObject *scope, expr_ty expr)
{
    PyObject *ret = NULL;
    PyObject *test = NULL, *body = NULL, *orelse = NULL;

    test = validate_expr(scope, expr->v.IfExp.test, GFalse);
    if (!test)
        goto fail;

    if (GarterType_Kind(test) != GT_BOOL) {
        Py_DECREF(test);
        Garter_ERROR(expr->v.IfExp.test,
                     "Invalid (non-bool) type for if expression test");
    }

    body = validate_expr(scope, expr->v.IfExp.body, GFalse);
    if (!body)
        goto fail;

    if (expr->v.IfExp.orelse) {
        orelse = validate_expr(scope, expr->v.IfExp.orelse, GFalse);
        if (!orelse)
            goto fail;

        if (!GarterType_Equal(body, orelse)) {
            Garter_ERROR(expr->v.IfExp.orelse,
                         "Type of else arm must match body arm");
        }
    }

    Py_INCREF(body);
    ret = body;
    goto finally;

fail:
    Py_XDECREF(ret);
    ret = NULL;
finally:
    Py_XDECREF(test);
    Py_XDECREF(body);
    Py_XDECREF(orelse);

    return ret;
}

static PyObject * /* owned */
validate_list_expr(PyObject *scope, expr_ty expr)
{
    PyObject *ret = NULL;

    /* XXX: Support the empty list literal (delayed type inference?) */
    asdl_seq *seq = expr->v.List.elts;
    PyObject *elt_type = NULL, *this_type = NULL;

    for (int i = 0; i < asdl_seq_LEN(seq); i++) {
        expr_ty elt = (expr_ty)asdl_seq_GET(seq, i);
        this_type = validate_expr(scope, elt, GFalse);
        if (!elt_type) {
            elt_type = this_type; /* transfer ownership */
            this_type = NULL;
            if (!elt_type)
                goto fail;
            continue;
        }
        
        if (!GarterType_Equal(this_type, elt_type)) {
            Garter_ERROR(expr,
                         "Arrays must all contain elements of the same "
                         "type. Element %d contained an inconsistent type",
                         i);
        }

        Py_DECREF(this_type);
        this_type = NULL;
    }

    /* elt_type may be null here - late-bound empty list */
    ret = GarterType_New(GT_LIST, elt_type);
    goto finally;

fail:
    Py_XDECREF(ret);
    ret = NULL;
finally:
    Py_XDECREF(elt_type);
    Py_XDECREF(this_type);
    return ret;
}

#if 0
static PyObject * /* owned */
validate_dict_expr(PyObject *scope, expr_ty expr)
{
    PyObject *ret = NULL;

    /* XXX: Support the empty list literal (delayed type inference?) */
    asdl_seq *seq = expr->v.List.elts;
    PyObject *elt_type = NULL, *this_type = NULL;

    for (int i = 0; i < asdl_seq_LEN(seq); i++) {
        expr_ty elt = (expr_ty)asdl_seq_GET(seq, i);
        this_type = validate_expr(scope, elt, GFalse);
        if (!elt_type) {
            elt_type = this_type; /* transfer ownership */
            if (!elt_type)
                goto fail;
            continue;
        }
        
        if (!GarterType_Equal(this_type, elt_type)) {
            Garter_ERROR(expr,
                         "Arrays must all contain elements of the same "
                         "type. Element %d contained an inconsistent type",
                         i);
        }

        Py_DECREF(this_type);
        this_type = NULL;
    }

    if (!elt_type) {
        Garter_ERROR(expr, "Empty list literals are not yet supported");
    }
    
    ret = GarterType_New(GT_LIST, elt_type);
    goto finally;

fail:
    Py_XDECREF(ret);
    ret = NULL;
finally:
    Py_XDECREF(elt_type);
    Py_XDECREF(this_type);
    return ret;
}
#else
static PyObject * /* owned */
validate_dict_expr(PyObject *scope, expr_ty expr)
{
    Garter_ERROR(expr, "ASD");
fail:
    return NULL;
}
#endif

static PyObject * /* owned */
validate_unaryop_expr(PyObject *scope, expr_ty expr)
{
    unaryop_ty op = expr->v.UnaryOp.op;
    expr_ty operand = expr->v.UnaryOp.operand;

    PyObject *ret = NULL;
    PyObject *operand_type = validate_expr(scope, operand, GFalse);
    if (!operand_type)
        goto fail;

    assert(GarterType_Check(operand_type));
    GarterTypeKind operand_kind = GarterType_Kind(operand_type);

    switch (op) {
    case Invert: {
        if (operand_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        }
        Garter_ERROR(expr, "Invalid operand to unary `~` operator");
    }
    case Not: {
        if (operand_kind == GT_BOOL) {
            INCREF_RET_FINALLY(GarterType_BOOL);
        }
        Garter_ERROR(expr, "Invalid operand to unary `not` operator");
    }
    case UAdd: {
        if (operand_kind == GT_INT || operand_kind == GT_FLOAT) {
            INCREF_RET_FINALLY(operand_type);
        }
        Garter_ERROR(expr, "Invalid operand to unary `+` operator");
    }
    case USub: {
        if (operand_kind == GT_INT || operand_kind == GT_FLOAT) {
            INCREF_RET_FINALLY(operand_type);
        }
        Garter_ERROR(expr, "Invalid operand to unary `-` operator");
    }
    default:
        assert(0);
    }

fail:
    ret = NULL;
finally:
    Py_XDECREF(operand_type);
    return ret;
}

static PyObject * /* owned */
validate_binop_expr(PyObject *scope, expr_ty expr)
{
    expr_ty lhs = expr->v.BinOp.left;
    operator_ty op = expr->v.BinOp.op;
    expr_ty rhs = expr->v.BinOp.right;

    PyObject *ret = NULL;
    PyObject *lhs_type = NULL, *rhs_type = NULL;

    lhs_type = validate_expr(scope, lhs, GFalse);
    if (!lhs_type)
        goto fail;
    rhs_type = validate_expr(scope, rhs, GFalse);
    if (!rhs_type)
        goto fail;

    assert(GarterType_Check(lhs_type) && GarterType_Check(rhs_type));
    GarterTypeKind lhs_kind = GarterType_Kind(lhs_type);
    GarterTypeKind rhs_kind = GarterType_Kind(rhs_type);

    switch (op) {
    case Add: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        } else if ((lhs_kind == GT_FLOAT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_INT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_FLOAT && rhs_kind == GT_INT)) {
            INCREF_RET_FINALLY(GarterType_FLOAT);
        } else if (lhs_kind == GT_STR && rhs_kind == GT_STR) {
            INCREF_RET_FINALLY(GarterType_STR);
        } else if (lhs_kind == GT_LIST &&
                   GarterType_Equal(lhs_type, rhs_type)) {
            INCREF_RET_FINALLY(lhs_type);
        }
        Garter_ERROR(expr, "Invalid type operands to `+` operator");
    }
    case Sub: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        } else if ((lhs_kind == GT_FLOAT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_INT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_FLOAT && rhs_kind == GT_INT)) {
            INCREF_RET_FINALLY(GarterType_FLOAT);
        }
        Garter_ERROR(expr, "Invalid type operands to `-` operator");
    }
    case Mult: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        } else if ((lhs_kind == GT_FLOAT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_INT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_FLOAT && rhs_kind == GT_INT)) {
            INCREF_RET_FINALLY(GarterType_FLOAT);
        }
        Garter_ERROR(expr, "Invalid type operands to `-` operator");
    }
    case MatMult: {
        Garter_ERROR(expr,
                     "Matrix multiplication operator `@` is not "
                     "supported by Garter");
    }
    case Div: {
        if ((lhs_kind == GT_INT || lhs_kind == GT_FLOAT) &&
            (rhs_kind == GT_INT || rhs_kind == GT_FLOAT)) {
            INCREF_RET_FINALLY(GarterType_FLOAT);
        }
        Garter_ERROR(expr, "Invalid type operands to `/` operator");
    }
    case Mod: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        } else if ((lhs_kind == GT_FLOAT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_INT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_FLOAT && rhs_kind == GT_INT)) {
            INCREF_RET_FINALLY(GarterType_FLOAT);
        }
        Garter_ERROR(expr, "Invalid type operands to `%` operator");
    }
    case Pow: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        } else if ((lhs_kind == GT_FLOAT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_INT && rhs_kind == GT_FLOAT) ||
                   (lhs_kind == GT_FLOAT && rhs_kind == GT_INT)) {
            INCREF_RET_FINALLY(GarterType_FLOAT);
        }
        Garter_ERROR(expr, "Invalid type operands to `**` operator");
    }
    case LShift: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        }
        Garter_ERROR(expr, "Invalid type operands to `<<` operator");
    }
    case RShift: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        }
        Garter_ERROR(expr, "Invalid type operands to `>>` operator");
    }
    case BitOr: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        }
        Garter_ERROR(expr, "Invalid type operands to `|` operator");
    }
    case BitXor: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        }
        Garter_ERROR(expr, "Invalid type operands to `^` operator");
    }
    case BitAnd: {
        if (lhs_kind == GT_INT && rhs_kind == GT_INT) {
            INCREF_RET_FINALLY(GarterType_INT);
        }
        Garter_ERROR(expr, "Invalid type operands to `&` operator");
    }
    case FloorDiv: {
        if ((lhs_kind == GT_INT || lhs_kind == GT_FLOAT) &&
            (rhs_kind == GT_INT || rhs_kind == GT_FLOAT)) {
            INCREF_RET_FINALLY(GarterType_INT);
        }
        Garter_ERROR(expr, "Invalid type operands to `//` operator");
    }
    default:
        assert(0);
    }

fail:
    ret = NULL;
finally:
    Py_XDECREF(lhs_type);
    Py_XDECREF(rhs_type);
    return ret;
}

static PyObject * /* owned */
validate_expr(PyObject *scope, expr_ty expr, GBoolean lvalue /* XXX use */)
{
    assert(expr);

    PyObject *ret = NULL;

    switch (expr->kind) {
    case Num_kind:
        if (PyLong_Check(expr->v.Num.n)) {
            INCREF_RET_FINALLY(GarterType_INT);
        } else if (PyFloat_Check(expr->v.Num.n)) {
            INCREF_RET_FINALLY(GarterType_FLOAT);
        } else {
            Garter_ERROR(expr, "Unrecognized number type!");
        }
    case JoinedStr_kind: /* XXX: What is a JoinedStr? Is this correct? */
    case Str_kind:
        INCREF_RET_FINALLY(GarterType_STR);
    case Name_kind: {
        PyObject *name = expr->v.Name.id;
        assert(PyUnicode_Check(name));

        PyObject *items = GarterScope_Items(scope);
        assert(PyDict_Check(items));

        ret = PyDict_GetItem(items, name);
        Py_XINCREF(ret);
        if (!ret)
            Garter_ERROR(expr, "Undefined identifier %V", name);

        goto finally;
    }
    case BoolOp_kind: {
        asdl_seq *seq = expr->v.BoolOp.values;
        for (int i = 0; i < asdl_seq_LEN(seq); i++) {
            expr_ty operand = (expr_ty)asdl_seq_GET(seq, i);
            PyObject *ty = validate_expr(scope, operand, GFalse);
            if (!ty)
                goto fail;

            if (GarterType_Kind(ty) != GT_BOOL) {
                Py_DECREF(ty);
                Garter_ERROR(operand, "Operands to BoolOp must be bool");
            }
            Py_DECREF(ty);
        }

        INCREF_RET_FINALLY(GarterType_BOOL);
    }
    case NameConstant_kind: {
        singleton value = expr->v.NameConstant.value;
        if (PyBool_Check(value)) {
            INCREF_RET_FINALLY(GarterType_BOOL);
        }

        Garter_ERROR(expr, "Unrecognized NameConstant");
    }
    case List_kind: {
        ret = validate_list_expr(scope, expr);
        goto finally;
    }
    case Dict_kind: {
        ret = validate_dict_expr(scope, expr);
        goto finally;
    }
    case BinOp_kind: {
        ret = validate_binop_expr(scope, expr);
        goto finally;
    }
    case UnaryOp_kind: {
        ret = validate_unaryop_expr(scope, expr);
        goto finally;
    }
    case IfExp_kind: {
        ret = validate_if_expr(scope, expr);
        goto finally;
    }

    default:
        Garter_ERROR(expr, "Unrecognized expression kind %d", expr->kind);
#if 0
    case Dict_kind:
    case Set_kind: /* XXX: support sets? */
    case Compare_kind:
    case Call_kind:
    case FormattedValue_kind: /* XXX: Support? probably not */
    case Bytes_kind: /* XXX: Support bytes? probably not */
    case Attribute_kind:
    case Subscript_kind:
    case Tuple_kind:
        ;
#endif
    }

fail:
    Py_XDECREF(ret);
    ret = NULL;
finally:
    assert(!ret || GarterType_Check(ret));
    return ret;
}

static GBoolean
validate_assign_stmt(PyObject *scope, stmt_ty stmt, GBoolean groot)
{
    assert(stmt->kind == Assign_kind);

    GBoolean ret = GFalse;
    asdl_seq *targets = stmt->v.Assign.targets;
    expr_ty value, type, target;
    PyObject *value_type = NULL, *target_type = NULL;

    value = stmt->v.Assign.value;
    type = stmt->v.Assign.type;

    if (asdl_seq_LEN(targets) != 1)
        Garter_ERROR(stmt,
                     "Assignments may only have a single target in garter");

    target = (expr_ty)asdl_seq_GET(targets, 0);
    if (!target) {
        PyErr_SetString(PyExc_ValueError, "None disallowed as a target");
        goto fail;
    }

    value_type = validate_expr(scope, value, GFalse);
    if (!value_type)
        goto fail;

    target_type = NULL;

    if (type) {
        if (type->kind == Ellipsis_kind) {
            Py_INCREF(value_type);
            target_type = value_type;
        } else {
            target_type = validate_type(scope, type);
            if (!target_type) {
                goto fail;
            }
        }
        if (!GarterType_IsComplete(target_type)) {
            Garter_ERROR(stmt, "Incomplete type in declaration");
        }

        if (!validate_decl_target(scope, target, target_type)) {
            goto fail;
        }

        if (!groot) {
            Garter_ERROR(stmt,
                         "Declarations must occur at the global level or in "
                         "function roots");
        }
    } else {
        target_type = validate_expr(scope, target, GFalse);
        if (!target_type) {
            goto fail;
        }
    }

    /* XXX: Subtyping */
    if (!GarterType_Equal(target_type, value_type))
        Garter_ERROR(value, "Incorrect type in assignment");

    ret = GTrue;

fail:
    Py_XDECREF(value_type);
    Py_XDECREF(target_type);

    return ret;
}

static GBoolean
validate_stmt(PyObject *scope, stmt_ty stmt, GBoolean sroot)
{
    switch (stmt->kind) {
    case FunctionDef_kind:
        UNIMPLEMENTED(stmt);
    case ClassDef_kind:
        UNIMPLEMENTED(stmt);
    case Return_kind:
        UNIMPLEMENTED(stmt);
    case Assign_kind:
        return validate_assign_stmt(scope, stmt, sroot);
    case AugAssign_kind: {
        /* Translate into phony assign statement and BinOp expression */
        struct _expr e = {BinOp_kind};
        e.v.BinOp.op = stmt->v.AugAssign.op;
        e.v.BinOp.left = stmt->v.AugAssign.target;
        e.v.BinOp.right = stmt->v.AugAssign.value;

        /* an asdl_seq object by itself contains enough space for one item */
        asdl_seq seq = {1, {stmt->v.AugAssign.target}};

        struct _stmt s = {Assign_kind};
        s.v.Assign.targets = &seq;
        s.v.Assign.value = &e;
        s.v.Assign.type = NULL;

        return validate_assign_stmt(scope, &s, sroot);
    }
    case If_kind: {
        PyObject *test = validate_expr(scope, stmt->v.If.test, GFalse);
        if (!test)
            goto fail;

        if (GarterType_Kind(test) != GT_BOOL) {
            Py_DECREF(test);
            Garter_ERROR(stmt->v.If.test,
                         "Invalid (non-bool) type for if expression test");
        }

        if (!validate_stmts(scope, stmt->v.If.body, GFalse)) {
            Py_DECREF(test);
            goto fail;
        }

        if (!validate_stmts(scope, stmt->v.If.orelse, GFalse)) {
            Py_DECREF(test);
            goto fail;
        }

        Py_DECREF(test);
        return GTrue;
    }
    case For_kind:
    case While_kind:
    case Assert_kind:
    case Global_kind:
    case Nonlocal_kind:
        UNIMPLEMENTED(stmt);
    case Expr_kind: {
        PyObject *expr = validate_expr(scope, stmt->v.Expr.value, GFalse);
        Py_XDECREF(expr);
        return expr != NULL;
    }
    case Break_kind:
    case Continue_kind:
        return GTrue;
    default:
        Garter_ERROR(stmt, "Statement kind not supported by Garter");
    }

fail:
    return GFalse;
}

static GBoolean
validate_stmts(PyObject *scope, asdl_seq *seq, GBoolean sroot)
{
    int i;
    for (i = 0; i < asdl_seq_LEN(seq); i++) {
        stmt_ty stmt = (stmt_ty)asdl_seq_GET(seq, i);
        if (stmt) {
            if (!validate_stmt(scope, stmt, sroot))
                return GFalse;
        }
        else {
            PyErr_SetString(PyExc_ValueError,
                            "None disallowed in statement list");
            return GFalse;
        }
    }
    return GTrue;
}

static GBoolean
validate_mod(PyObject *scope, mod_ty mod)
{
    GBoolean res = GFalse;

    switch (mod->kind) {
    case Module_kind:
        res = validate_stmts(scope, mod->v.Module.body, GTrue);
        break;
    case Interactive_kind:
        res = validate_stmts(scope, mod->v.Interactive.body, GTrue);
        break;
    case Expression_kind: {
        PyObject *type = validate_expr(scope, mod->v.Expression.body, GFalse);
        Py_XDECREF(type);
        res = type != NULL;
        break;
    }
    case Suite_kind:
        PyErr_SetString(PyExc_ValueError, "Suite is not valid in the CPython compiler");
        break;
    default:
        PyErr_SetString(PyExc_SystemError, "impossible module node");
        break;
    }
    return res;
}

PyObject * /* owned */
Garter_NewGlobalScope()
{
    PyObject *scope = GarterScope_New(NULL);
    if (!scope) /* XXX: Set error */
        return NULL;

    /* PyObject *items = GarterScope_Items(scope); */

    /* XXX: Insert standard global scope items here */
    /*
    PyDict_SetItemString(items, "int",
                         GarterType_New(GT_TYPE, GarterType_INT));
    PyDict_SetItemString(items, "float",
                         GarterType_New(GT_TYPE, GarterType_FLOAT));
    PyDict_SetItemString(items, "bool",
                         GarterType_New(GT_TYPE, GarterType_BOOL));
    PyDict_SetItemString(items, "str",
                         GarterType_New(GT_TYPE, GarterType_STR));
    */

    return scope;
}

int
Garter_Validate(mod_ty mod, PyObject *filename, PyObject *scope)
{
    if (!GarterScope_Check(scope)) {
        PyErr_SetString(PyExc_ValueError,
                        "Expected GarterScope object as scope argument "
                        "to Garter_Validate()");
        return GFalse;
    }

    if (!PyUnicode_Check(filename)) {
        PyErr_SetString(PyExc_ValueError,
                        "Expected Unicode object as filename argument "
                        "to Garter_Validate()");
        return GFalse;
    }

    PyObject *bkp = GarterScope_ValidationBegin(scope, filename);

    Py_INCREF(scope);
    GBoolean success = validate_mod(scope, mod);
    Py_DECREF(scope);

    if (success) {
        GarterScope_ValidationOk(scope);
    } else {
        GarterScope_ValidationFail(scope, bkp);
    }

    return success;
}

