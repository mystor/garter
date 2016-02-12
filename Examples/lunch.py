print("I Know an Old Lady")

animal := ["fly", "spider", "bird", "cat", "dog", "goat", "cow", "horse"]
remark := [
    "I don't know why she swallowed a fly.",
	"That wiggled and jiggled and tickled inside her.",
	"How absurd, to swallow a bird.",
	"Imagine that, she swallowed a cat.",
	"What a hog, to swallow a dog.",
	"What a dope, to swallow a goat.",
	"I don't know how she swallowed that cow.",
	"She died of course.",
]

for a in range(8):
    print()
    print("I know an old lady")
    print("Who swallowed a", animal[a])
    print(remark[a])

    for n in range(a, 0, -1):
        print("She swallowed the", animal[n], "to catch the", animal[n-1] + ",")

    if a > 0:
        print(remark[0])
    if a < 7:
        print("Perhaps she'll die.")

print()
print("The end.")
