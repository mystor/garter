import random

while True:
    x := random.random()
    print(x, "\t",
          "Hi ho, hi ho" if x > 0.5 else "It's off to work we go")
