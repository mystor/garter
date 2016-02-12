MAXPRIME := 1000


flags : {int: bool} = {}
for i in range(2, MAXPRIME):
    flags[i] = True

factor := 1
while True:
    if factor > MAXPRIME: break
    idx := factor + 1
    while idx < MAXPRIME and flags[idx] != True:
        idx += 1
    factor = idx

    multiplier := 2
    idx = multiplier * factor
    while idx < MAXPRIME:
        flags[idx] = False
        multiplier += 1
        idx = multiplier * factor

print("The prime numbers from 2 to", MAXPRIME, "are:")
for i in range(2, MAXPRIME):
    if flags[i]:
        print(i, end=" ")
print()

