def palin(s : str) -> str:
    if s == "":
        return ""
    else:
        return s[0] + palin(s[1:]) + s[0]

while True:
    word := input("Please give me a word: ")
    print("Its palindrome is:", palin(word))
    if word == "quit":
        break
