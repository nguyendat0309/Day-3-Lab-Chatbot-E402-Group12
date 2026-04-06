import json
from pprint import pprint
def MyData(path):
   with open(path, 'r', encoding="utf-8") as fo:
       data = json.load(fo)
       return data

