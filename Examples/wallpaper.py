def right():
    print("""
\\   \\   \\   \\   \\   \\   \\   \\
 \\   \\   \\   \\   \\   \\   \\   \\
  \\   \\   \\   \\   \\   \\   \\   \\
   \\   \\   \\   \\   \\   \\   \\   \\""")

def left():
    print("""
   /   /   /   /   /   /   /   /
  /   /   /   /   /   /   /   /
 /   /   /   /   /   /   /   /
/   /   /   /   /   /   /   /""")

def exes():
    print("""
\\  /\\  /\\  /\\  /\\  /\\  /\\  /\\  /
 \\/  \\/  \\/  \\/  \\/  \\/  \\/  \\/
 /\\  /\\  /\\  /\\  /\\  /\\  /\\  /\\
/  \\/  \\/  \\/  \\/  \\/  \\/  \\/  \\""")

print("Please type l, r, or x, any number of times")

for c in input():
    if c == "l":
        left()
    elif c == "r":
        right()
    elif c == "x":
        exes()
    else:
        break
