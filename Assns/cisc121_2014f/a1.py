def rectangular(lst : [[int]]) -> bool:
    if len(lst) == 0:
        return True # Empty rectangle is rectangular
    width := len(lst[0])
    for row in lst:
        if len(row) != width:
            return False
    return True

def rotate(lst : [[int]]) -> [[int]]:
    if len(lst) == 0:
        return []
    # XXX: We could technically infer these types from usage potentially?
    result : [[int]] = []
    col : [int] = []
    for y in range(len(lst[0])):
        for row in lst:
            col.append(row[y])
        result.append(col)
    return result

def Opish(s : str) -> str:
    out := ""
    last_non_vowel := "foo"
    for char in s:
        if char in ['a', 'e', 'i', 'o', 'u']:
            if last_non_vowel:
                out += 'op'
            last_non_vowel = False
        else:
            last_non_vowel = True
        out += char
    return out
