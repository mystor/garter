width := int(input("Enter box width: "))
height := int(input("Enter box height: "))
nacross := int(input("enter number of boxes across: "))
ndown := int(input("enter number of boxes down: "))

top := ""
middle := ""
bottom := ""
for i in range(width * nacross + 1):
    if i % width == 0:
        top += " "
        middle += "|"
        bottom += "|"
    else:
        top += "_"
        middle += " "
        bottom += "_"

print(top)

for i in range(ndown):
    for j in range(height):
        print(middle)
    print(bottom)
