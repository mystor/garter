ordinal := ["first", "second", "third", "fourth", "fifth", "sixth",
            "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]

gift := [
    "A partridge in a pear tree.", "Two turtle doves, and",
	"Three french hens,", "Four calling birds,", "Five golden rings,",
	"Six geese a-laying,", "Seven swans a-swimming,",
	"Eight maids a milking,", "Nine ladies dancing,",
	"Ten lords a-leaping,", "Eleven pipers piping,",
	"Twelve drummers drumming,"
]

print("The Twelve Days of Christmas")

for day in range(len(gift)):
    print()
    print("On the " + ordinal[day] + " day of Christmas")
    print("My true love sent to me,")
    gifts := gift[:day+1]
    gifts.reverse()
    for g in gifts:
        print(g)

print()
print("The end.")
