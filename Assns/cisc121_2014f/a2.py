def matrixMax(heat : [[int]]) -> int:
    max_heat := 0
    for row in heat:
        for it in row:
            if it > max_heat:
                max_heat = it
    return max_heat

def matrixMin(heat : [[int]]) -> int:
    min_heat := 100
    for row in heat:
        for it in row:
            if it < min_heat:
                min_heat = it
    return min_heat

def visitNeighbors(m : [[int]], fn : bool(int, int, int, [int])):
    w := len(m)
    h := len(m[0])

    for x in range(w):
        for y in range(h):
            val := m[x][y]
            neighbors : [int] = []
            for nx in [x-1, x, x+1]:
                if nx < 0 or nx > w:
                    continue
                for ny in [y-1, y, y+1]:
                    if ny < 0 or ny > h:
                        continue
                    neighbors.append(m[nx][ny])
            if fn(x, y, val, neighbors):
                return


def matrixCheck(heat : [[int]], errors : bool) -> bool:
    w := len(heat)
    h := len(heat[0])
    result := True

    def visitor(x : int, y : int, it : int, neighbors : [int]):
        nonlocal result
        for h in neighbors:
            if h - it < -2:
                result = False
                if errors:
                    print("Value in row ", x, "column", y,
                            "is much hotter than its neighbours")
            elif h - it > 2:
                result = False
                if errors:
                    print("Value in row ", x, "column", y,
                            "is much colder than its neighbours")
        return False

    visitNeighbors(heat, visitor)
    return result

def tempLocations(heat : [[int]], temp : int) -> [[int]]:
    res : [[int]] = []
    for row in heat:
        nrow : [int] = []
        for it in row:
            nrow.append(1 if it >= temp else 0)
        res.append(nrow)
    return res

def tempBoundaries(heat : [[int]]) -> [[int]]:


#def tempBoundaries(heat : [[int]]) -> [[int]]:
    #nheat := heat[:]
    #for i in range(len(nheat)):
        #nheat[i] = nheat[i][:]


