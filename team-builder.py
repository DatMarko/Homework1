import requests

# Build a team of up to 6 Pokémon and summarize common weaknesses.
# This script queries the public PokeAPI to get each Pokémon's types,
# then looks up type damage relations to compute damage multipliers.

# Counter for how many Pokémon are weak to each type (counts 2x and 4x only)
weakness_count = {}

# Separate counter for when a Pokémon is 4x weak to a type (both types share the
# same weakness and their multipliers multiply to 4)
four_x_weakness_count = {}

# We'll collect the chosen team names for a final printout
team = []

# Ask for up to 6 Pokémon names
i = 0
while i < 6:
    name = input("Enter a Pokemon name: ")

    # Query the Pokémon endpoint (case-insensitive name is supported by API)
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")

    # Basic error handling for misspelled names
    if response.status_code == 404:
        print(f"Pokemon '{name}' not found. Check your spelling.")
    else:
        data = response.json()

        # The Pokémon can have one or two types; `types` is a list
        types = data["types"]

        # `multipliers` will map an attacking type name -> numeric multiplier
        # Example values: 2 (super effective), 0.5 (resisted), 0 (immune).
        # If the Pokémon has two types, multipliers for the same attacking type
        # are multiplied together (e.g., 2 * 2 = 4 if both types are weak).
        multipliers = {}

        for t in types:
            type_name = t["type"]["name"]
            print("Pokemon types are: " + type_name)

            # Look up the type's damage relations which list which types
            # deal double, half, or no damage to this type.
            response2 = requests.get(f"https://pokeapi.co/api/v2/type/{type_name}")
            data2 = response2.json()

            double_damage = data2["damage_relations"]["double_damage_from"]
            half_damage = data2["damage_relations"]["half_damage_from"]
            no_damage = data2["damage_relations"]["no_damage_from"]

            # For each attacking type that does double damage to this defender type,
            # multiply the current multiplier by 2 (or set it to 2 if not seen yet).
            # Reasoning: if a Pokémon has two types and both are weak to the same
            # attacking type, multipliers multiply (2 * 2 = 4).
            for weakness in double_damage:
                current_type = weakness["name"]

                if current_type in multipliers:
                    multipliers[current_type] *= 2
                else:
                    multipliers[current_type] = 2

            # For resistances, multiply by 0.5 (halved damage). If later the same
            # attacking type is also a weakness from the other defender type, the
            # values multiply (for example, 2 * 0.5 = 1 -> neutral overall).
            for resistance in half_damage:
                current_type = resistance["name"]

                if current_type in multipliers:
                    multipliers[current_type] *= 0.5
                else:
                    multipliers[current_type] = 0.5

            # Immunities override other multipliers and set damage to 0.
            # Example: a Ground attack does 0 damage to Flying types.
            for immunity in no_damage:
                current_type = immunity["name"]
                multipliers[current_type] = 0

        # After processing all defender types, `multipliers` contains the combined
        # damage multipliers for every attacking type against this Pokémon.
        # We now increment counters for 2x and 4x weaknesses so we can see which
        # attacking types are common threats across the assembled team.
        for current_weakness in multipliers:
            # Only count clear weaknesses (2x and 4x). Resistances and immunities
            # are ignored for the team weakness summary.
            if multipliers[current_weakness] == 2:
                if current_weakness in weakness_count:
                    weakness_count[current_weakness] += 1
                else:
                    weakness_count[current_weakness] = 1

                print(f"Added 2x {current_weakness} for {name} — count is now {weakness_count[current_weakness]}")

            elif multipliers[current_weakness] == 4:
                # A 4x weakness occurs when both defender types are weak to the
                # same attacking type: 2 * 2 = 4. We count it both in the general
                # `weakness_count` and separately in `four_x_weakness_count`.
                if current_weakness in weakness_count:
                    weakness_count[current_weakness] += 1
                else:
                    weakness_count[current_weakness] = 1

                if current_weakness in four_x_weakness_count:
                    four_x_weakness_count[current_weakness] += 1
                else:
                    four_x_weakness_count[current_weakness] = 1

                print(f"Added 4x {current_weakness} for {name} — count is now {weakness_count[current_weakness]}")

        # Keep the chosen Pokémon name and move to the next slot in the team
        team.append(name)
        i += 1


print(team)
print("Weakness count:")
print(weakness_count)

print("4x weakness count:")
print(four_x_weakness_count)