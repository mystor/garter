# Evaluate an input expression e of the form t { + t } where
#     t is of form { * p } and p is of form ( e ) or explicit real constant
# For example, the value of 1.5 + 3.0 * ( 0.5 + 1.5 ) "halt" is 7.5

def expn(tokens : [str]) -> float:
    v := term(tokens)
    while tokens[0] == "+":
        tokens.pop(0)
        v += term(tokens)
    return v

def term(tokens : [str]) -> float:
    v := primary(tokens)
    while tokens[0] == "*":
        tokens.pop(0)
        v *= primary(tokens)
    return v

def primary(tokens : [str]) -> float:
    v := 0.0
    if tokens[0] == "(":
        tokens.pop(0)
        v = expn(tokens)
        assert tokens[0] == ")"
    else:
        v = float(tokens[0])
    tokens.pop(0)
    return v

print("This is a recursive evaluator for infix expressions.")
print("The only operators accepted are + and *, as well as parentheses.")
print("Besides that, everything has to be separated by blanks.")
print("Terminate an expression by anything handy, such as a single period.")
print("Be gentle, this is just a demo of Garter mutual recursion.")
print()

while True:
    print()
    print("Give an arithmetic expression, with operators surrounded by blanks")
    tokens := input().split(" ")
    answer := expn(tokens)
    print("Answer is:", answer)

