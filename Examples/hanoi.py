def hanoi(n : int, s : str, d : str, i : str):
    if n == 0:
        return

    hanoi(n - 1, s, i, d)
    print("Move disc", n, "from", s, "to", d)
    hanoi(n - 1, i, d, s)

hanoi(5, "left", "right", "centre")
