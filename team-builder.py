import requests

i=0
team=[]
weaknesses=[]
weakness_count = {}
four_x_weakness_count = {}
while i < 6:
    name = input("Enter a Pokemon name: ")
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")

    if response.status_code == 404:
        print(f"Pokemon '{name}' not found. Check your spelling.")
    else:
        data = response.json()
        types = data["types"]
        multipliers = {}

        for t in types:
            type_name = t["type"]["name"]
            print("Pokemon types are: " + type_name)

            response2 = requests.get(f"https://pokeapi.co/api/v2/type/{type_name}")
            data2 = response2.json()

            double_damage = data2["damage_relations"]["double_damage_from"]
            half_damage = data2["damage_relations"]["half_damage_from"]
            no_damage = data2["damage_relations"]["no_damage_from"]

            for weakness in double_damage:
                current_type = weakness["name"]

                if current_type in multipliers:
                    multipliers[current_type] *= 2
                else:
                    multipliers[current_type] = 2

            for resistance in half_damage:
                current_type = resistance["name"]

                if current_type in multipliers:
                    multipliers[current_type] *= 0.5
                else:
                    multipliers[current_type] = 0.5

            for immunity in no_damage:
                current_type = immunity["name"]
                multipliers[current_type] = 0

        for current_weakness in multipliers:
            if multipliers[current_weakness] == 2:
                if current_weakness in weakness_count:
                    weakness_count[current_weakness] += 1
                else:
                    weakness_count[current_weakness] = 1

                print(f"Added 2x {current_weakness} for {name} — count is now {weakness_count[current_weakness]}")

            elif multipliers[current_weakness] == 4:
                if current_weakness in weakness_count:
                    weakness_count[current_weakness] += 1
                else:
                    weakness_count[current_weakness] = 1

                if current_weakness in four_x_weakness_count:
                    four_x_weakness_count[current_weakness] += 1
                else:
                    four_x_weakness_count[current_weakness] = 1

                print(f"Added 4x {current_weakness} for {name} — count is now {weakness_count[current_weakness]}")

        team.append(name)
        i += 1

print(team)
print("Weakness count:")
print(weakness_count)

print("4x weakness count:")
print(four_x_weakness_count)