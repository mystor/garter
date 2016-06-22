"""
Start a python-like interactive interpereter for garter code.
Uses code.py's logic, with the InteractiveConsole replaced with
garter's logic.
"""

from code import InteractiveConsole
from gartercodeop import CommandCompiler
import readline
import sys
import garter

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
        with open(filename) as f:
            source = f.read()
        codeob = garter.gcompile(source, filename)
        exec(codeob)
    else:
        console = InteractiveConsole()
        console.compile = CommandCompiler() # Substitute in garter's command compiler
        console.interact("Garter 0.0.1 Interactive Interpereter")
