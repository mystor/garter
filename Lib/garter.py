"""
Validation Module for the Garter programming language.

It has 2 entry points, the Scope constructor, for creating your own global
scope, and the gcompile function, which acts as an analogue to compile(),
except that it also validates garter code in the process.

Originally, the validation module was written in C, to try to access more of
cpython's internals as part of the implementation. When it was realized that
this was unnecessary for the desired results, the validation module was ported
to python, as it would allow for the implementation to be implemented much
faster.

The lack of type-checking in the python module is easily made up for by how the
C module had to use Python objects (which aren't type-safe) anyways, meaning
that most type checks were relegated to runtime anyways.

Performance is also not a concern for Garter programs, due to their small size.
"""

import ast
import re

_filename = None # Set by the compile function
def GarterError(node, body):
    """
    Produce an error object which can be thrown to represent an error.
    XXX: Make this better and probably have a custom class for the error.
    """
    # XXX: This should work better
    # XXX: Actually include the text property, and have it set correctly
    return SyntaxError(body, (_filename, node.lineno, node.col_offset, None))
    return error


class Ty:
    def completes(self, other):
        """
        True if the type self is a more or equally complete type than other,
        else False
        """
        return self == other

    def __eq__(self, other):
        self.subsumes(other) and other.subsumes(self)


class TyInt(Ty):
    def is_complete(self):
        return True

    def subsumes(self, other):
        return type(other) == TyInt

    def __repr__(self):
        return 'int'
TY_INT = TyInt() # Singleton instance


class TyFloat(Ty):
    def is_complete(self):
        return True

    def subsumes(self, other):
        return type(other) == TyFloat or \
            type(other) == TyInt

    def __repr__(self):
        return 'float'
TY_FLOAT = TyFloat() # Singleton instance


class TyBool:
    def is_complete(self):
        return True

    def subsumes(self, other):
        return type(other) == TyBool

    def __repr__(self):
        return 'bool'
TY_BOOL = TyBool() # Singleton instance


class TyStr:
    def is_complete(self):
        return True

    def subsumes(self, other):
        return type(other) == TyStr

    def __repr__(self):
        return 'str'
TY_STR = TyStr() # Singleton instance


class TyDict:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def is_complete(self):
        return self.key != None and self.value != None and \
               self.key.is_complete() and self.value.is_complete()

    def subsumes(self, other):
        return self.completes(other)

    def completes(self, other):
        if type(other) != TyDict:
            return False
        if other.key == None and other.value == None:
            return True
        return self.key.completes(other.key) and \
            self.value.completes(other.value)

    def __eq__(self, other):
        if not isinstance(other, TyDict):
            return False
        return self.key == other.key and \
            self.value == other.value

    def __repr__(self):
        return '{{{}: {}}}'.format(self.key, self.value)


class TyList:
    def is_complete(self):
        return self.item != None and self.item.is_complete()

    def __init__(self, item):
        self.item = item

    def subsumes(self, other):
        return self.completes(other)

    def completes(self, other):
        if type(other) != TyList:
            return False
        if other.item == None:
            return True
        return self.item.completes(other.item)

    def __repr__(self):
        return '[{}]'.format(self.item)


class TyClass:
    def is_complete(self):
        return self.fields != None

    def __init__(self, fields):
        self.fields = fields

    def subsumes(self, other):
        # XXX: Subclassing
        if type(other) != TyClass:
            return False
        return self.completes(other)

    def completes(self, other):
        if type(other) != TyClass:
            return False
        return other.fields == None or \
            self.fields is other.fields

    def __repr__(self):
        return 'class '.format(self.item)


class TyFunc:
    def is_complete(self):
        return True

    def __init__(self, ret, args):
        self.ret = ret
        self.args = args

    # Subsumption on functions:
    # e.g. (int, int) -> float subsumes (float, float) -> int
    # (float, float) -> int does not subsume (int, int) -> float
    # As a float is not a legal argument to (int, int) -> float,
    # and the return value isn't necessarially an int

    def subsumes(self, other):
        if type(other) != TyFunc:
            return False
        if len(self.args) != len(other.args):
            return False
        # If we return a more general value,
        if not self.ret.subsumes(other.ret):
            return False
        # And accept more specific values
        for sarg, oarg in zip(self.args, other.args):
            if not oarg.subsumes(sarg):
                return False
        # Then we are more general!
        return True

    def __eq__(self, other):
        if not isinstance(other, TyFunc):
            return False
        return self.ret == other.ret and \
            self.args == other.args


def subsume(a, b):
    """
    Return the more general of the two types, or None if the types
    do not match.
    """
    if a.subsumes(b):
        return a
    elif b.subsumes(a):
        return b
    # XXX: Find a c such that c.subsumes(a) and c.subsumes(b)?
    return None


class Variable:
    def __init__(self, ty, mutable, init):
        self.ty = ty
        self.mutable = mutable
        self._init = init

    def init(self):
        if self._init == None:
            return
        self._init() # Maybe pass self?
        self._init = None
        return


class VariableInfo:
    def __init__(self, var, local, globl):
        self.ty = var.ty
        self.mutable = var.mutable
        self.local = local
        self.globl = globl


class Scope:
    """
    A given scope in the Garter programming language. Used for each scope,
    starting from the root and going up to inner scopes such as function scopes.
    """

    def __init__(self, up=None, root=False):
        self.up = up
        self.root = root
        self.vars = {}
        self.classes = {}
        if up == None: # Global Scope - definitely a root (override)
            self.root = True
        self._func = None # The current function type, set by validate_funcdef

    def func(self):
        """
        Returns the type of the function the scope is within
        """
        curr = self
        while curr._func == None:
            if curr == None:
                return None
            curr = curr.up
        return curr._func

    def declare(self, name, ty, mutable=True, init=None):
        """
        Declares a variable with the name name. Returns True if the declaration
        succeeded, False if it failed.
        XXX: Produce more useful results for better error messages?
        """
        assert type(name) is str

        # Check if it is in this scope or any non-root parents
        curr = self
        while True:
            if name in curr.vars:
                return False
            if curr.root: break
            curr = curr.up

        self.vars[name] = Variable(ty, mutable, init)
        return True

    def lookup(self, name):
        """
        Looks up a variable. Returns a VariableInfo object.
        None is returned if there is no variable with the given name.
        Initializes the variable with init() before returning
        If the variable has an associated init, and has not been init-ed,
        invokes that function.
        """
        local = True
        curr = self
        while curr != None:
            if name in curr.vars:
                curr.vars[name].init()
                return VariableInfo(curr.vars[name], local, curr.up == None)
            if curr.root:
                local = False
            curr = curr.up
        return None

    def declare_class(self, name, fields):
        """
        XXX: Allow class definitions outside of the very top level?
        """
        raise NotImplementedError()

    def backup(self):
        assert self.up == None
        return {
            'vars': self.vars.copy(),
            'classes': self.classes.copy(),
        }

    def restore(self, backup):
        assert self.up == None
        self.vars = backup['vars']
        self.classes = backup['classes']

    def flush(self):
        for var in self.vars.values():
            var.init()


# Garter defines keywords which aren't present in Python. We need to reject
# these keywords whenever they are present as identifiers in unintended places
keyword_re = re.compile(r'__.+__|' # Starting and ending with __ => keyword
                        r'int|float|bool|str|' # Type keywords
                        r'len|range|print') # Magic Functions
def ensure_non_keyword(name):
    if isinstance(name, ast.Name):
        name = name.id
    if keyword_re.match(name):
        raise GarterError(name, "Expected identifier, "
                          "instead found keyword {}".format(name))


def validate_type(scope, expr):
    if type(expr) == ast.Name:
        # Check for the valid keyword types
        if expr.id == 'int':
            return TY_INT
        elif expr.id == 'float':
            return TY_FLOAT
        elif expr.id == 'str':
            return TY_STR
        elif expr.id == 'bool':
            return TY_BOOL

        # XXX: Classes
        ensure_non_keyword(expr)
        raise GarterError(expr, "Unrecognized type name {}", expr.id)

    if type(expr) == ast.Dict:
        if len(expr.keys) != 1 or len(expr.values) != 1:
            raise GarterError(expr,
                              "Dictionary types list a single key-value type pair")
        key = validate_type(scope, expr.keys[0])
        value = validate_type(scope, expr.values[0])
        return TyDict(key, value)

    if type(expr) == ast.List:
        if len(expr.elts) != 1:
            raise GarterError(expr,
                              "List types may only have a single type listed")
        elt = validate_type(scope, expr.elts[0])
        return TyList(elt)

    raise GarterError(expr, "Malformed type")


def validate_boolop(scope, expr):
    for value in expr.values:
        ty = validate_expr(scope, value)
        if not TY_BOOL.subsumes(ty):
            # XXX: Print the actual type?
            raise GarterError(expr,
                              "Operands to and/or expressions must be bools")
    return TY_BOOL


def validate_binop(scope, expr):
    lhs = validate_expr(scope, expr.left)
    rhs = validate_expr(scope, expr.right)

    op = type(expr.op)
    if op is ast.Add:
        if TY_INT.subsumes(lhs) and TY_INT.subsumes(rhs):
            return TY_INT
        elif TY_FLOAT.subsumes(lhs) and TY_FLOAT.subsumes(rhs):
            return TY_FLOAT
        elif TY_STR.subsumes(lhs) and TY_STR.subsumes(rhs):
            return TY_STR
        elif type(lhs) is TyList and type(rhs) is TyList:
            item = subsumes(lhs.item, rhs.item)
            if item != None:
                return TyList(item)
        raise GarterError(expr, "Invalid operands to +: {} and {}".format(lhs, rhs))
    elif op is ast.Sub:
        if TY_INT.subsumes(lhs) and TY_INT.subsumes(rhs):
            return TY_INT
        elif TY_FLOAT.subsumes(lhs) and TY_FLOAT.subsumes(rhs):
            return TY_FLOAT
        raise GarterError(expr, "Invalid operands to -: {} and {}".format(lhs, rhs))
    elif op is ast.Mult:
        if TY_INT.subsumes(lhs) and TY_INT.subsumes(rhs):
            return TY_INT
        elif TY_FLOAT.subsumes(lhs) and TY_FLOAT.subsumes(rhs):
            return TY_FLOAT
        raise GarterError(expr, "Invalid operands to *: {} and {}".format(lhs, rhs))
    elif op is ast.Div:
        if TY_FLOAT.subsumes(lhs) and TY_FLOAT.subsumes(rhs):
            return TY_FLOAT
        raise GarterError(expr, "Invalid operands to /: {} and {}".format(lhs, rhs))
    elif op is ast.Mod:
        if TY_INT.subsumes(lhs) and TY_INT.subsumes(rhs):
            return TY_INT
        elif TY_FLOAT.subsumes(lhs) and TY_FLOAT.subsumes(rhs):
            return TY_FLOAT
        raise GarterError(expr, "Invalid operands to %: {} and {}".format(lhs, rhs))
    elif op is ast.Pow:
        if TY_FLOAT.subsumes(lhs) and TY_FLOAT.subsumes(rhs):
            return TY_FLOAT
        raise GarterError(expr, "Invalid operands to **: {} and {}".format(lhs, rhs))
    elif op is ast.FloorDiv:
        if TY_INT.subsumes(lhs) and TY_INT.subsumes(rhs):
            return TY_INT
        elif TY_FLOAT.subsumes(lhs) and TY_FLOAT.subsumes(rhs):
            return TY_FLOAT
        raise GarterError(expr, "Invalid operands to //: {} and {}".format(lhs, rhs))

    raise GarterError(expr, "Unrecognized binary operator")


def validate_unaryop(scope, expr):
    operand = validate_expr(scope, expr.operand)

    op = type(expr.op)
    if op is ast.Not:
        if TY_BOOL.subsumes(operand):
            return TY_BOOL
        raise GarterError(expr, "Invalid operand to not: {}".format(operand))
    elif op is ast.UAdd:
        if TY_FLOAT.subsumes(operand):
            return operand
        raise GarterError(expr, "Invalid operand to +: {}".format(operand))
    elif op is ast.USub:
        if TY_FLOAT.subsumes(operand):
            return operand
        raise GarterError(expr, "Invalid operand to -: {}".format(operand))

    raise GarterError(expr, "Unrecognized unary operator")


def validate_ifexp(scope, expr):
    test = validate_expr(scope, expr.test)
    if not TY_BOOL.subsumes(test):
        raise GarterError(expr.test,
                          "Test in if expression must have type bool")
    then = validate_expr(scope, expr.body)
    orelse = validate_expr(scope, expr.orelse)

    result = subsume(then, orelse)
    if result == None:
        raise GarterError(expr, "Type of else arm must match body arm")
    return result


def validate_dict(scope, expr):
    key = None
    value = None
    for (kvalue, vvalue) in zip(expr.keys, expr.values):
        key_ty = validate_expr(scope, kvalue)
        value_ty = validate_expr(scope, vvalue)
        if key == None:
            key = key_ty
            value = value_ty
            continue
        if not key.subsumes(key_ty):
            if key_ty.subsumes(key):
                key = key_ty
            else:
                raise GarterError(kvalue, "Mismatched Types: Dicts must "
                                  "contain consistent key types")
        if not value.subsumes(value_ty):
            if value_ty.subsumes(value):
                value = value_ty
            else:
                raise GarterError(vvalue, "Mismatched Types: Dicts must "
                                  "contain consistent key types")
    return TyDict(key, value)


def validate_list(scope, expr):
    elt = None
    for value in expr.elts:
        ty = validate_expr(scope, value)
        if elt == None:
            elt = ty
            continue
        if not elt.subsumes(ty):
            if ty.subsumes(elt):
                elt = ty # e.g. [1, 2.3] is [float]
                continue
            raise GarterError(expr, "Mismatched Types: Arrays must contain "
                              "consistent element types.")
    return TyList(elt) # Works even if elt is None
    

def validate_expr(scope, expr, lvalue = False):
    # Confirm that it is valid in the lvalue context
    if lvalue and not (isinstance(expr, ast.Name) or
                       isinstance(expr, ast.Subscript) or
                       isinstance(expr, ast.Attribute)):
        raise GarterError(expr, "Can only assign to names, "
                            "attributes, and subscriptions")

    if isinstance(expr, ast.Num):
        if isinstance(expr.n, int):
            return TY_INT
        return TY_FLOAT

    elif isinstance(expr, ast.JoinedStr) or \
         isinstance(expr, ast.Str):
        return TY_STR

    elif isinstance(expr, ast.Name):
        ensure_non_keyword(expr)
        var = scope.lookup(expr.id)
        if var == None:
            raise GarterError(expr, "No variable with name {} in scope".format(expr.id))
        if lvalue:
            if not var.mutable:
                raise GarterError(expr, "Cannot assign to {}, as it is "
                                  "non-mutable")
            if not var.local:
                raise GarterError(expr, "Cannot assign to {}, as it is "
                                  "non-local. Try using the `nonlocal` or "
                                  "`global` statement to expose it in this scope")
        return var.ty

    elif isinstance(expr, ast.BoolOp):
        return validate_boolop(scope, expr)

    elif isinstance(expr, ast.NameConstant):
        if isinstance(expr.value, bool):
            return TY_BOOL
        raise GarterError(expr, "Unrecognized NameConstant")

    elif isinstance(expr, ast.List):
        return validate_list(scope, expr)

    elif isinstance(expr, ast.Dict):
        return validate_dict(scope, expr)

    elif isinstance(expr, ast.BinOp):
        return validate_binop(scope, expr)

    elif isinstance(expr, ast.UnaryOp):
        return validate_unaryop(scope, expr)

    elif isinstance(expr, ast.IfExp):
        return validate_ifexp(scope, expr)

    raise GarterError(expr, "Unrecognized expression kind")


def validate_assign(scope, stmt):
    if len(stmt.targets) != 1:
        raise GarterError(stmt, "Assignments may only have a single "
                          "target in garter")
    value_ty = validate_expr(scope, stmt.value)
    target_ty = None

    target = stmt.targets[0]
    if stmt.type: # Declaration!
        # Determine type of the declaration
        if isinstance(stmt.type, ast.Ellipsis): # Ellipsis == placeholder (:=)
            target_ty = value_ty
        else:
            target_ty = validate_type(scope, stmt.type)
        if not target_ty.is_complete():
            raise GarterError(stmt, "Incomplete type in declaration")

        # Validate the target of the declaration
        assert isinstance(target, ast.expr)
        if isinstance(target, ast.Name):
            ensure_non_keyword(target)
            if not scope.declare(target.id, target_ty):
                raise GarterError(target, "Variable with name {} has "
                                  "already been defined".format(target.id))
        else:
            raise GarterError(target, "Complex expressions are not "
                                "legal on the left hand side of a variable "
                                "declaration")
    else: # Standard assignment
        target_ty = validate_expr(scope, target, True)

    if not target_ty.subsumes(value_ty):
        raise GarterError(stmt, "Invalid type in assignment")


def validate_augassign(scope, stmt):
    # XXX: Don't do this in the sketchy way used here, as it produces
    # awful error messages...

    # Build a series of fake "equivalent" ast nodes
    binop = ast.BinOp()
    binop.op = stmt.op
    binop.left = stmt.target
    binop.right = stmt.value
    binop.lineno = stmt.lineno
    binop.col_offset = stmt.col_offset

    assign = ast.Assign()
    assign.targets = [stmt.target]
    assign.value = binop
    assign.type = None
    assign.lineno = stmt.lineno
    assign.col_offset = stmt.col_offset

    validate_assign(scope, assign)


def validate_if(scope, stmt):
    """
    Returns true if both branches of the if unconditionally return
    """
    test = validate_expr(scope, stmt.test)
    if not TY_BOOL.subsumes(test):
        raise GarterError(stmt.test,
                          "Test in if statement must have type bool")
    # We 
    return validate_scoped(scope, stmt.body) and \
        validate_scoped(scope, stmt.orelse)


def validate_print(scope, stmt):
    pass


def validate_while(scope, stmt):
    test = validate_expr(scope, stmt.test)
    if not TY_BOOL.subsumes(test):
        raise GarterError(stmt.test,
                          "Test in if statement must have type bool")
    validate_scoped(scope, stmt.body)
    if len(stmt.orelse) > 0:
        raise GarterError(stmt, "An else block is not permitted on while statements")


def validate_range(scope, expr):
    pass


def validate_for(scope, stmt):
    if not type(stmt.target) is ast.Name:
        raise GarterError(stmt, "For loop target must be a name")

    if len(stmt.orelse) > 0:
        raise GarterError(stmt, "An else block is not permitted on for statements")

    # Check for the range psuedo-function
    item_ty = None
    if type(stmt.iter) is ast.Call and \
       type(stmt.iter.func) is ast.Name and \
       stmt.iter.func.id == "range":
        item_ty = validate_range(scope, stmt.iter)
    else:
        list_ty = validate_expr(scope, stmt.iter)
        if type(list_ty) != TyList:
            raise GarterError(stmt, "Expected [?], instead found {}".format(list_ty))
        item_ty = list_ty.item

    # Introduce the inner scope
    inner = Scope(scope)
    ensure_non_keyword(stmt.target)
    if not inner.declare(stmt.target.id, item_ty):
        raise GarterError(stmt.target, "Variable with name {} has "
                          "already been defined".format(stmt.target.id))
    validate_stmts(inner, stmt.body)
    inner.flush()


def validate_assert(scope, stmt):
    test = validate_expr(stmt.test)
    if not TY_BOOL.subsumes(test):
        raise GarterError(stmt, "Condition to assert statement must be bool")
    if stmt.msg != None:
        msg = validate_expr(stmt.msg)
        if not TY_STR.subsumes(msg):
            raise GarterError(stmt, "Assert message must be str")


def validate_funcdef(scope, stmt):
    # Make sure we have a valid function name
    ensure_non_keyword(stmt.name)
    if len(stmt.decorator_list) > 0:
        raise GarterError(stmt, "Decorators are not supported")

    # XXX: This is ugly - not sure what the best way to handle this would be
    returns = validate_type(scope, returns) if returns != None else None

    # Make sure we aren't using any unsupported features
    arguments = stmt.arguments
    if arguments.vararg != None:
        raise GarterError(stmt, "Varargs are not supported")
    if arguments.kwarg != None:
        raise GarterError(stmt, "Kwards are not supported")
    if len(arguments.defaults) > 0 or len(arguments.kw_defaults) > 0:
        raise GarterError(stmt, "Default arguments are not supported")
    if len(arguments.kwonlyargs) > 0:
        raise GarterError(stmt, "Keyword only arguments are not supported")

    # Determine the types of arguments
    arg_tys = []
    inner = Scope(scope, root=True)
    for arg in arguments.args:
        ensure_non_keyword(arg.arg)
        if arg.annotation == None:
            raise GarterError(arg, "Type annotations on arguments are required")
        ty = validate_type(scope, arg.annotation)
        arg_tys.append(ty) # Record the type of the argument
        if not inner.declare(arg.arg, ty):
            raise GarterError(arg, "There is another argument with name {}".format(arg))

    # Define the variable in scope for the function
    fty = TyFunc(returns, arg_tys)
    def func_init():
        # XXX: Discover locals?
        inner._func = fty
        validate_stmts(inner, stmt.body)
        # Flush all functions declared within this function!
        inner.flush()
    scope.declare(stmt.name, fty, mutable=False, init=func_init)


def validate_stmt(scope, stmt):
    """
    Validates that a statement is correct.
    Returns True if the statement unconditionally returned.
    """
    assert isinstance(stmt, ast.stmt)

    kind = type(stmt)
    if kind is ast.FunctionDef:
        validate_funcdef(scope, stmt)
        return False

    elif kind is ast.ClassDef:
        raise NotImplementedError()

    elif kind is ast.Return:
        raise NotImplementedError()

    elif kind is ast.Assign:
        validate_assign(scope, stmt)
        return False

    elif kind is ast.AugAssign:
        validate_augassign(scope, stmt)
        return False

    elif kind is ast.If:
        return validate_if(scope, stmt)

    elif kind is ast.For:
        validate_for(scope, stmt)
        return False

    elif kind is ast.While:
        validate_while(scope, stmt)
        return False

    elif kind is ast.Assert:
        validate_assert(scope, stmt)
        return False

    elif kind is ast.Nonlocal or kind is ast.Global:
        raise GarterError(stmt, "nonlocal and global statements must be the "
                          "first statements in a function definition")

    elif kind is ast.Expr:
        # Check if we're looking at the print statement
        if type(stmt.value) is ast.Call and \
           type(stmt.value.func) is ast.Name and \
           stmt.value.func.id == "print":
            validate_print(scope, stmt.value)
        else:
            # Otherwise do normal validation logic
            validate_expr(scope, stmt.value)
        return False

    elif kind is ast.Break or \
         kind is ast.Continue:
        # Python already checks if we are in a loop in its validation pass,
        # so, we don't have to check that here!
        pass

    elif kind is ast.Pass:
        # Pass statements are allowed anywhere!
        return False

    else:
        raise GarterError(stmt, "Statement kind not supported")


def validate_stmts(scope, stmts):
    """
    Validate the listed statements within the scope
    Returns true if the statements listed unconditionally return
    """
    returns = False
    for stmt in stmts:
        if returns:
            raise GarterError(stmt, "Unreachable code after statement which "
                              "unconditionally returns")
        if validate_stmt(scope, stmt):
            returns = True
    return returns


def validate_scoped(scope, stmts):
    """
    Introduce a new non-root scope, and validate the listed statements within it
    Returns True if the statements listed unconditionally return
    """
    inner = Scope(scope)
    ret = validate_stmts(inner, stmts)
    inner.flush() # Validate all functions within the scope
    return ret


def validate_mod(scope, mod):
    assert isinstance(mod, ast.mod)
    kind = type(mod)
    if kind is ast.Module:
        validate_stmts(scope, mod.body)
    elif kind is ast.Interactive:
        validate_stmts(scope, mod.body)
    elif kind is ast.Expression:
        validate_expr(scope, mod.body)
    else:
        raise GarterError(mod, "Invalid module type")


def validate(mod, scope):
    backup = scope.backup()
    try:
        validate_mod(scope, mod)
    except:
        scope.restore(backup)
        raise


# A Python compile-function like entry point for the program!
def gcompile(source,
             filename='<unknown>',
             mode='exec',
             flags=0,
             dont_inherit=False,
             optimize=-1,
             global_scope=None):
    """
    Not named `compile`, such that the built in compile function is
    callable from this module, as we need to be able to compile it.
    """
    if not isinstance(source, ast.AST):
        return gcompile(ast.parse(source, filename, mode),
                        filename, mode, flags, dont_inherit,
                        optimize, global_scope)

    # Create a default scope if one isn't provided for this invocation
    if not global_scope:
        global_scope = Scope()

    # Record the filename information for error reporting purposes
    global _filename
    _filename = filename

    # Ensure we have a valid global scope object
    if global_scope.up != None or not global_scope.root:
        raise TypeError("Unexpected non-toplevel scope!")
    try:
        # XXX: Discover locals
        validate(source, global_scope)
    finally:
        _filename = None

    # Compile the object itself.
    return compile(source, filename, mode, flags, dont_inherit, optimize)

