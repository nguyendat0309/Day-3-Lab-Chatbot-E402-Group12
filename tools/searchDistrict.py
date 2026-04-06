def searchDistrict(data, district):
    result = []
    for d in data:
        if d["district"] == district:
            result.append(d)
    return result


