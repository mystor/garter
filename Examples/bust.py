# Blackjack Simulation Program
# Based on the bust.t program written for the
# Turing programming language By J.R. Cordy

import random

joe_naives_guts := 0
players_name := ""
games_played := 0
deck : [int] = []

class Player:
    hand : [int] = []
    count := 0
    won := 0
    stops := False

dealer := Player()
player := Player()

def initialize():
    # print program explanation
    print("""
This program simulates the game of blackjack.

The dealer plays the compulsory strategy of standing on 17, or better.

The player plays either
    (1) The standard naive strategy of standing on n or better, or
    (2) A simplified version of the strategy described by  E.O.Thorp
        in his book 'Beat the Dealer' (Vintage Books, 1966) pp. 20-21.
Input :
    For each shuffle, a player name (character string of <= 20 characters),
    and if the player name specified is not 'E.O.Thorp', the count (n)
    on which the player stands.

If the player name specified is 'E.O.Thorp', the player strategy used
will be Thorp's.
Otherwise, the player will use the standard stop on count > n strategy.

The program will simulate one complete shuffle of play for each player.""")

card_names := ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

def hand_image(hand : [int]) -> str:
    image := ""
    for card in hand:
        image += " " + card_names[card-1]
    return image

def somebody_plays() -> bool:
    global joe_naives_guts, players_name

    print("New shuffle.")
    players_name = input("Enter player name (q to quit): ")

    if players_name == "q":
        return False

    if players_name != "E.O.Thorp":
        joe_naives_guts = input("What does he stand on? ")
        while not 0 < joe_naives_guts < 21:
            joe_naives_guts = int(input("(1..20): "))

    if players_name == "E.O.Thorp":
        print("E.O.Thorp plays this time")
    else:
        print("Next player is " + players_name + ".")
        print("He stops at " + str(joe_naives_guts) + ".")

    if joe_naives_guts < 15:
        print("(What a hamburger!)")
    else:
        print("Good luck, " + players_name + ".")

    return True

def shuffle():
    counts : {int:int} = {}

    deck.clear()
    for n_cards in range(52):
        card := random.randint(1, 13)
        while counts.get(card, 0) == 4:
            card = random.randint(1, 13)

        deck.append(card)
        counts[card] = counts.get(card, 0) + 1

def playing() -> bool:
    global games_played

    if len(deck) > 10:
        print("\nNew game.")
        games_played += 1
        return True
    else:
        print("\nToo few cards left for another game")
        print("Of", games_played, "games,", players_name,
              "won", player.won, "and dealer won", dealer.won)

        if dealer.won > player.won:
            print("House cleans up on", players_name, "this time.")
        elif player.won > dealer.won:
            if players_name == "E.O.Thorp":
                print("E.O.Thorp does it again.")
            else:
                print(players_name, "must have doctored the shuffle.")
        else:
            print("Even Shuffle.")

        return False


def player_takes_a_card():
    player.hand.append(deck.pop(-1))

def dealer_takes_a_card():
    dealer.hand.append(deck.pop(-1))

def deal():
    player.stops = False
    dealer.stops = False

    player.hand = []
    dealer.hand = []
    for i in range(2):
        player_takes_a_card()
        dealer_takes_a_card()

    print("The initial deal gives", players_name, ":", hand_image(player.hand))
    print("The initial deal gives the dealer :", hand_image(dealer.hand))

class Evaluation:
    soft_hand := False
    value := 0

def evaluate(hand : [int]) -> Evaluation:
    n_aces_counted_11 := 0
    evaluation := Evaluation()

    for card in hand:
        if card > 1 and card < 11:
            evaluation.value += card
        elif card == 1:
            evaluation.value += 11
            n_aces_counted_11 += 1
        else:
            evaluation.value += 10

    while evaluation.value > 21 and n_aces_counted_11 != 0:
        evaluation.value -= 10
        n_aces_counted_11 -= 1

    evaluation.soft_hand = n_aces_counted_11 > 0
    return evaluation

def dealer_move():
    evaluation := evaluate(dealer.hand)
    dealer.count = evaluation.value

    if dealer.count > 21:
        print("Dealer goes bust.")
        dealer.stops = True
        player.won += 1
        return
    elif dealer.count == 21:
        print("Dealer calls blackjack.")
        dealer.stops = True
        dealer.won += 1
        return

    if dealer.count < 17:
        dealer_takes_a_card()
    else:
        dealer.stops = True

    if dealer.stops:
        print("Dealer stands with", dealer.count)

        if dealer.count > player.count:
            print("House wins.")
            dealer.won += 1
        elif dealer.count < player.count:
            print(players_name, "wins.")
            player.won += 1
        else:
            print("Tie game.")
    else:
        print("Dealer takes a card and now has", hand_image(dealer.hand))

def player_joe_naive():
    if player.count < joe_naives_guts:
        player_takes_a_card()
    else:
        player.stops = True

def player_thorp(soft_hand : bool):
    dealer_shows := dealer.hand[0]

    if soft_hand:
        if dealer_shows > 8:
            player.stops = player.count > 18
        else:
            player.stops = player.count > 17
    else:
        if 1 < dealer_shows < 4:
            player.stops = player.count > 12
        elif 3 < dealer_shows < 7:
            player.stops = player.count > 11
        else:
            player.stops = player.count > 16

    if not player.stops:
        player_takes_a_card()


def player_move():
    evaluation := evaluate(player.hand)
    player.count = evaluation.value

    if player.count < 21:
        if players_name == "E.O.Thorp":
            player_thorp(evaluation.soft_hand)
        else:
            player_joe_naive()
    elif player.count > 21:
        print(players_name, "goes bust.")
        player.stops = True
        dealer.stops = True
        dealer.won += 1
        return
    else:
        print(players_name, "calls blackjack.")
        player.stops = True
        dealer.stops = True
        player.won += 1
        return

    if player.stops:
        print(players_name, "stands with", player.count)
    else:
        print(players_name, "takes a card and now has", hand_image(player.hand))

initialize()
while somebody_plays():
    shuffle()
    while playing():
        deal()
        while not player.stops:
            player_move()
        while not dealer.stops:
            dealer_move()
