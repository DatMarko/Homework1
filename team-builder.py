import requests

response = requests.get("https://pokeapi.co/api/v2/pokemon/pikachu")
data = response.json()

types = data["types"]
for t in types:
    print(t["type"]["name"])