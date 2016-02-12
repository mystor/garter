while True:
    infinitive := input("Please give me a regular French 'er' verb: ")
    print("Thanks, here is the present conjugation")
    root := infinitive[:-2]
    print("The root of this verb is '" + root + "'")
    if infinitive[-2:] == "er":
        if root[0] not in "aeiou":
            print("Je " + root + "e")
        else:
            print("J'" + root + "e")

        print("Tu " + root + "es")
        print("Il " + root + "e")
        print()
        if root[-1] == "g":
            print("Nous " + root + "eons")
        else:
            print("Nous " + root + "ons")
        print("Vous " + root + "ez")
        print("Ils " + root + "ent")
        print()
    elif infinitive[-2:] == "ir":
        print("I'm too tired to do an 'ir' verb")
    else:
        print("I don't like the looks of this verb")
