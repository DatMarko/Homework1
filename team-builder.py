import requests

i=0
team=[]
while i < 6:
    name = input("Enter a Pokemon name: ")
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")
    if response.status_code == 404:
        print(f"Pokemon '{name}' not found. Check your spelling.")
    else:
        data = response.json()
        types = data["types"]
        for t in types:
            print(t["type"]["name"])
        i = i + 1
        team.append(name)
        
        
print(team)