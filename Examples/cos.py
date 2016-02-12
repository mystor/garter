import math

x := 0.0
for i in range(100):
    print("cos(", x, ")**2 + sin(", x, ")**2 =", math.cos(x) ** 2 + math.sin(x) ** 2)
    x += 13
