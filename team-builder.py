import requests


def get_pokemon_multipliers(pokemon_name):
    """Return damage multipliers for each attacking type against a Pokémon."""
    normalized_name = pokemon_name.strip().lower()
    response = requests.get(
        f"https://pokeapi.co/api/v2/pokemon/{normalized_name}",
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    multipliers = {}

    for type_entry in data["types"]:
        type_name = type_entry["type"]["name"]
        type_response = requests.get(f"https://pokeapi.co/api/v2/type/{type_name}", timeout=10)
        type_response.raise_for_status()
        type_data = type_response.json()

        for weakness in type_data["damage_relations"]["double_damage_from"]:
            multipliers[weakness["name"]] = multipliers.get(weakness["name"], 1) * 2

        for resistance in type_data["damage_relations"]["half_damage_from"]:
            multipliers[resistance["name"]] = multipliers.get(resistance["name"], 1) * 0.5

        for immunity in type_data["damage_relations"]["no_damage_from"]:
            multipliers[immunity["name"]] = 0

    return multipliers


def format_name(name):
    """Return a cleaner display name for a Pokémon."""
    return name.strip().title()


def update_team_summary(team_name, multipliers, weakness_count, four_x_weakness_count, weakness_contributors):
    display_name = format_name(team_name)
    for attack_type, multiplier in multipliers.items():
        if multiplier == 2:
            weakness_count[attack_type] = weakness_count.get(attack_type, 0) + 1
            weakness_contributors[attack_type] = weakness_contributors.get(attack_type, "") + (
                ", " if weakness_contributors.get(attack_type, "") else ""
            ) + display_name

        elif multiplier == 4:
            weakness_count[attack_type] = weakness_count.get(attack_type, 0) + 1
            four_x_weakness_count[attack_type] = four_x_weakness_count.get(attack_type, 0) + 1
            weakness_contributors[attack_type] = weakness_contributors.get(attack_type, "") + (
                ", " if weakness_contributors.get(attack_type, "") else ""
            ) + display_name


def main():
    weakness_count = {}
    four_x_weakness_count = {}
    weakness_contributors = {}
    team = []

    while len(team) < 6:
        name = input("Enter a Pokémon name (or press Enter to finish): ").strip()
        if not name:
            break

        normalized_name = name.strip().lower()
        if any(member.lower() == normalized_name for member in team):
            print("That Pokémon is already in your team. Please choose a different one.")
            continue

        try:
            multipliers = get_pokemon_multipliers(name)
        except requests.RequestException as exc:
            print(f"Could not fetch Pokémon '{name}': {exc}")
            print("Please enter a valid Pokémon name.")
            continue

        update_team_summary(
            name,
            multipliers,
            weakness_count,
            four_x_weakness_count,
            weakness_contributors,
        )
        team.append(format_name(name))

    print("Team:", team)
    print("Weakness count:")
    for weakness, count in sorted(weakness_count.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {weakness}: {count}")

    print("\n4x weakness count:")
    for weakness, count in sorted(four_x_weakness_count.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {weakness}: {count}")

    print("\nWeakness contributors:")
    for weakness, contributors in sorted(weakness_contributors.items(), key=lambda item: item[0]):
        print(f"  {weakness}: {contributors}")


if __name__ == "__main__":
    main()