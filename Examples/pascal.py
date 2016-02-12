def addto(idx : int):
    if idx == 0:
        pascal[0] += 1
    else:
        pascal[idx] += pascal[idx - 1]

pascal := [1]
for i in range(14):
    pascal.append(0)

print("1")
for row in range(1, 15):
    for col in range(row, -1, -1):
        addto(col)
    for col in range(0, row + 1):
        print(str(pascal[col]), end="\t")
    print()
