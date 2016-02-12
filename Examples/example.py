# This is a version of the program from the second edition of Hume/Holt
# illustrating different programming languages.
# The program can be run interactively by typing in the data.
# See page 292 and following of book.

# This is a comment
while True:
    cost := float(input())
    life := int(input())
    print("cost =", cost, "life =", life)
    deprec := cost / life
    balance := cost
    for year in range(life):
        balance -= deprec
        print(year, "\t", balance)
