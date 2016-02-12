# Solution of Quadratic Equations

# This procedure solves quadratic equations to the
# current precision.  Results are returned in r1 and r2.
# Interpretation of the results depends on the result
# indicator ind in the following way:

#	ind	interpretation
#	***	**************

#	 0	no roots; r1=r2=huge

#	 1	one real root r1; r2=huge

#	 2	two real roots r1 and r2

#	 3	two complex roots c1=(r1,r2) and c2=(r1,-r2)

import math

class Results:
    r1 := 0.0
    r2 := 0.0
    ind := 0

def Quadratic(a : float, b : float, c : float) -> Results:
    res := Results()

    huge := 1e37

    if a == 0:
        if b == 0:
            res.ind = 0
        else:
            res.ind = 1
            res.r1 = - c / b

    else:
        disc := b * b - 4 * a * c
        if disc >= 0:
            res.ind = 2
            if b >= 0:
                res.r1 = (- b - math.sqrt(disc)) / (2 * a)
            else:
                res.r1 = (- b + math.sqrt(disc)) / (2 * a)

            if res.r1 == 0:
                res.r2 = 0
            else:
                res.r2 = c / (res.r1 * a)
        else:
            res.ind = 3
            res.r1 = - b / a
            res.r2 = math.sqrt(abs(disc)) / (2 * a)
    return res

print("Quadratic Equation Solver")

while True:
    a := float(input("a = "))
    b := float(input("b = "))
    c := float(input("c = "))

    res := Quadratic(a, b, c)

    if res.ind == 0:
        print("No roots")
    elif res.ind == 1:
        print("One real root r1 =", res.r1)
    elif res.ind == 2:
        print("Two real roots r1 =", res.r1, ", r2 =", res.r2)
    elif res.ind == 3:
        print("Two complex roots c1 = (", res.r1, ",", res.r2, "),",
              "c2 = (", res.r1, ",", - res.r2, ")")


