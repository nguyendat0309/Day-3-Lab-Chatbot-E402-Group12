
def searchPrice(data, minp, maxp):
    result = []
    for d in data:
        if d["price_avg"] >= minp and d["price_avg"] <= maxp:
            result.append(d)
    return result



