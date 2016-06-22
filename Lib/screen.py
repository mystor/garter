# Turing+ implementation of the Turing standard character screen operations
# J.R. Cordy, Queen's University
# February 2016

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self):
        c = self.impl()
        if c == "\e":
            c = self.impl()
            c = self.impl()
            if c == "A":
                c = UPARROW
            elif c == "B":
                c = DOWNARROW
            elif c == "C":
                c = RIGHTARROW
            elif c == "D":
                c = LEFTARROW
        return c

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

# Screen Modes
NORMALMODE = 0
SCREENMODE = 1
ECHO = 2
NOECHO = -2
CURSOR = 3
NOCURSOR = -3
NORMALINPUT = 4
KEYINPUT = -4
MAPCRNL = 5
NOMAPCRNL = -5

# Color Codes
BLACK = 0
RED = 1
GREEN = 2
BROWN = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
WHITE = 7
CLEAR = 8

# Color shifts
FOREGROUND = 30
BACKGROUND = 40

# Escape character
ESC = chr (27)

# Arrow key codes
UPARROW = chr (24)
DOWNARROW = chr (25)
RIGHTARROW = chr (26)
LEFTARROW = chr (27)

def write(*arg):
    x = ""
    for a in arg:
        x += a

    print(x, end="")


def setscreen (mode):
    #external def system (command: string)

    if mode == NORMALMODE:
        exec("stty sane")
    elif mode == SCREENMODE:
        exec("stty cbreak -echo")
    elif mode == ECHO:
        exec("stty echo")
    elif mode == NOECHO:
        exec("stty -echo")
    elif mode == CURSOR:
        pass
    elif mode == NOCURSOR:
        pass
    elif mode == NORMALINPUT:
        exec("stty -cbreak")
    elif mode == KEYINPUT:
        exec("stty cbreak")
    elif mode == MAPCRNL:
        pass
    elif mode == NOMAPCRNL:
        pass
    else:
        print("***ERROR: setscreen(): no such mode")
        exit(99)


def cls():
    write(ESC, "[0m")
    write(ESC, "[2J")
    write(ESC, "[;H")


def locate (row, col):
    write(ESC, "[")
    write(row, ";", col)
    write("H")


def hasch():
    #external def thasch : boolean
    return thasch()


def color (c):
    if c == CLEAR:
        write(ESC, "[0m")
    else:
        write(ESC, "[", FOREGROUND + c, "m")



def colorback (c: int):
    if c == CLEAR:
        write(ESC, "[0m")
    else:
        write(ESC, "[", BACKGROUND + c, "m")


def delay (ms):
    #external def usleep (us: int)
    #external "TL_TLI_TLIFS" def flushstreams
    flushstreams ()
    usleep (ms * 1000)

cls()
