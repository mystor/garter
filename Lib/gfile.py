import sys
import traceback
from garter import gcompile


def showsyntaxerror(filename=None):
    """Display the syntax error that just occurred.

    This doesn't display a stack trace because there isn't one.

    If a filename is given, it is stuffed in the exception instead
    of what was there before (because Python's parser always uses
    "<string>" when reading from a string).

    The output is written by sys.stderr.write(), below.

    """
    type, value, tb = sys.exc_info()
    sys.last_type = type
    sys.last_value = value
    sys.last_traceback = tb
    if filename and type is SyntaxError:
        # Work hard to stuff the correct filename in the exception
        try:
            msg, (dummy_filename, lineno, offset, line) = value.args
        except ValueError:
            # Not the format we expect; leave it alone
            pass
        else:
            # Stuff in the right filename
            value = SyntaxError(msg, (filename, lineno, offset, line))
            sys.last_value = value
    if sys.excepthook is sys.__excepthook__:
        lines = traceback.format_exception_only(type, value)
        sys.stderr.write(''.join(lines))
    else:
        # If someone has set sys.excepthook, we let that take precedence
        # over sys.stderr.write
        sys.excepthook(type, value, tb)

def showtraceback():
    """Display the exception that just occurred.

    We remove the first stack item because it is our own code.

    The output is written by sys.stderr.write(), below.

    """
    sys.last_type, sys.last_value, last_tb = ei = sys.exc_info()
    sys.last_traceback = last_tb
    try:
        lines = traceback.format_exception(ei[0], ei[1], last_tb.tb_next)
        if sys.excepthook is sys.__excepthook__:
            sys.stderr.write(''.join(lines))
        else:
            # If someone has set sys.excepthook, we let that take precedence
            # over sys.stderr.write
            sys.excepthook(ei[0], ei[1], last_tb)
    finally:
        last_tb = ei = None

if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename) as f:
        try:
            code = gcompile(f.read(), filename, 'exec')
            try:
                exec(code, {})
            except SystemExit:
                raise
            except:
                showtraceback()
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            showsyntaxerror(filename)

