import requests

i=0
team=[]
weaknesses=[]
while i < 6:
    name = input("Enter a Pokemon name: ")
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")

    if response.status_code == 404:
        print(f"Pokemon '{name}' not found. Check your spelling.")
    else:
        data = response.json()
        types = data["types"]
        for t in types:
            type_name = t["type"]["name"]
            print("Pokemon types are: " + t["type"]["name"])
            response2 = requests.get(f"https://pokeapi.co/api/v2/type/{type_name}")
            data2 = response2.json()
            
            weakness = data2["damage_relations"]["double_damage_from"]
        
            for t in weakness:
                print("weakness is: " + t["name"])
            

        team.append(name)
        
        
print(team)