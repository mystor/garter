r"""Utilities to compile possibly incomplete Python source code.

This module provides two interfaces, broadly similar to the builtin
function compile(), which take program text, a filename and a 'mode'
and:

- Return code object if the command is complete and valid
- Return None if the command is incomplete
- Raise SyntaxError, ValueError or OverflowError if the command is a
  syntax error (OverflowError and ValueError can be produced by
  malformed literals).

Approach:

First, check if the source consists entirely of blank lines and
comments; if so, replace it with 'pass', because the built-in
parser doesn't always do the right thing for these.

Compile three times: as is, with \n, and with \n\n appended.  If it
compiles as is, it's complete.  If it compiles with one \n appended,
we expect more.  If it doesn't compile either way, we compare the
error we get when compiling with \n or \n\n appended.  If the errors
are the same, the code is broken.  But if the errors are different, we
expect more.  Not intuitive; not even guaranteed to hold in future
releases; but this matches the compiler's behavior from Python 1.4
through 2.2, at least.

Caveat:

It is possible (but not likely) that the parser stops parsing with a
successful outcome before reaching the end of the source; in this
case, trailing symbols may be ignored instead of causing an error.
For example, a backslash followed by two newlines may be followed by
arbitrary garbage.  This will be fixed once the API for the parser is
better.

The two interfaces are:

compile_command(source, filename, symbol):

    Compiles a single command in the manner described above.

CommandCompiler():

    Instances of this class have __call__ methods identical in
    signature to compile_command; the difference is that if the
    instance compiles program text containing a __future__ statement,
    the instance 'remembers' and compiles all subsequent program texts
    with the statement in force.

The module also provides another class:

Compile():

    Instances of this class act like the built-in function compile,
    but with 'memory' in the sense described above.
"""

import __future__
import garter

_features = [getattr(__future__, fname)
             for fname in __future__.all_feature_names]

__all__ = ["Compile", "CommandCompiler"]

PyCF_DONT_IMPLY_DEDENT = 0x200          # Matches pythonrun.h

def _maybe_compile(compiler, source, filename, symbol, scope):
    # Check for source consisting of only blank lines and comments
    for line in source.split("\n"):
        line = line.strip()
        if line and line[0] != '#':
            break               # Leave it alone
    else:
        if symbol != "eval":
            source = "pass"     # Replace it with a 'pass' statement

    err = err1 = err2 = None
    code = code1 = code2 = None

    # Try to compile it as-is, we take a back up just in case
    backup = scope.backup()
    try:
        code = compiler(source, filename, symbol, scope)
    except SyntaxError as err:
        pass

    if code:
        return code
    scope.restore(backup) # We decided not to compile

    # These compiler outputs will not be used - so we restore the old value when done

    backup = scope.backup()
    try:
        code1 = compiler(source + "\n", filename, symbol, scope)
    except SyntaxError as e:
        err1 = e
    scope.restore(backup)

    backup = scope.backup()
    try:
        code2 = compiler(source + "\n\n", filename, symbol, scope)
    except SyntaxError as e:
        err2 = e
    scope.restore(backup)

    if not code1 and repr(err1) == repr(err2):
        raise err1

class Compile:
    """Instances of this class behave much like the built-in compile
    function, but if one is used to compile text containing a future
    statement, it "remembers" and compiles all subsequent program texts
    with the statement in force."""
    def __init__(self):
        self.flags = PyCF_DONT_IMPLY_DEDENT

    def __call__(self, source, filename, symbol, scope):
        # XXX: Also "remember" scopes etc.
        codeob = garter.gcompile(source, filename, symbol, self.flags, 1, scope=scope)
        for feature in _features:
            if codeob.co_flags & feature.compiler_flag:
                self.flags |= feature.compiler_flag
        return codeob

class CommandCompiler:
    """Instances of this class have __call__ methods identical in
    signature to compile_command; the difference is that if the
    instance compiles program text containing a __future__ statement,
    the instance 'remembers' and compiles all subsequent program texts
    with the statement in force."""

    def __init__(self,):
        self.compiler = Compile()
        self.scope = garter.new_global_scope() # A fresh global scope

    def __call__(self, source, filename="<input>", symbol="single"):
        r"""Compile a command and determine whether it is incomplete.

        Arguments:

        source -- the source string; may contain \n characters
        filename -- optional filename from which source was read;
                    default "<input>"
        symbol -- optional grammar start symbol; "single" (default) or
                  "eval"

        Return value / exceptions raised:

        - Return a code object if the command is complete and valid
        - Return None if the command is incomplete
        - Raise SyntaxError, ValueError or OverflowError if the command is a
          syntax error (OverflowError and ValueError can be produced by
          malformed literals).
        """
        return _maybe_compile(self.compiler, source, filename, symbol, self.scope)
