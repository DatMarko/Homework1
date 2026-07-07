import requests

TYPE_CACHE = {}
POKEMON_MULTIPLIER_CACHE = {}


def get_pokemon_multipliers(pokemon_name):
    """Return damage multipliers for each attacking type against a Pokémon."""
    normalized_name = pokemon_name.strip().lower()
    if normalized_name in POKEMON_MULTIPLIER_CACHE:
        return POKEMON_MULTIPLIER_CACHE[normalized_name]

    response = requests.get(
        f"https://pokeapi.co/api/v2/pokemon/{normalized_name}",
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    multipliers = {}

    for type_entry in data["types"]:
        type_name = type_entry["type"]["name"]

        if type_name not in TYPE_CACHE:
            type_response = requests.get(f"https://pokeapi.co/api/v2/type/{type_name}", timeout=10)
            type_response.raise_for_status()
            TYPE_CACHE[type_name] = type_response.json()

        type_data = TYPE_CACHE[type_name]

        for weakness in type_data["damage_relations"]["double_damage_from"]:
            multipliers[weakness["name"]] = multipliers.get(weakness["name"], 1) * 2

        for resistance in type_data["damage_relations"]["half_damage_from"]:
            multipliers[resistance["name"]] = multipliers.get(resistance["name"], 1) * 0.5

        for immunity in type_data["damage_relations"]["no_damage_from"]:
            multipliers[immunity["name"]] = 0

    POKEMON_MULTIPLIER_CACHE[normalized_name] = multipliers
    return multipliers


def format_name(name):
    """Return a cleaner display name for a Pokémon."""
    return name.strip().title()


def update_team_summary(
    team_name,
    multipliers,
    weakness_count,
    four_x_weakness_count,
    weakness_contributors,
    resistance_count,
    resistance_contributors,
):
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

        elif multiplier in (0.5, 0):
            resistance_count[attack_type] = resistance_count.get(attack_type, 0) + 1
            resistance_contributors[attack_type] = resistance_contributors.get(attack_type, "") + (
                ", " if resistance_contributors.get(attack_type, "") else ""
            ) + display_name


def get_defensive_type_suggestions(weakness_type):
    """Return types that resist or are immune to a given weakness type."""
    suggestions = []
    for type_id in range(1, 19):
        if type_id not in TYPE_CACHE:
            response = requests.get(f"https://pokeapi.co/api/v2/type/{type_id}", timeout=10)
            response.raise_for_status()
            TYPE_CACHE[type_id] = response.json()

        data = TYPE_CACHE[type_id]

        for resisted_type in data["damage_relations"]["half_damage_from"]:
            if resisted_type["name"] == weakness_type:
                suggestions.append(data["name"])
                break

        for immune_type in data["damage_relations"]["no_damage_from"]:
            if immune_type["name"] == weakness_type:
                suggestions.append(data["name"])
                break

    return sorted(set(suggestions))


def format_suggestion(types, max_items=5):
    if not types:
        return "no obvious defensive type"
    if len(types) == 1:
        return f"a {types[0]} type"
    if len(types) == 2:
        return f"a {types[0]} or {types[1]} type"
    preview = types[:max_items]
    if len(types) > max_items:
        return f"a {', '.join(preview[:-1])}, or {preview[-1]} type"
    return f"a {', '.join(preview[:-1])}, or {preview[-1]} type"


def get_relevant_weaknesses(weakness_count, four_x_weakness_count):
    """Return only the most important weaknesses for team-wide suggestions."""
    relevant = []
    for weakness, count in weakness_count.items():
        is_4x = four_x_weakness_count.get(weakness, 0) > 0
        if count >= 2 or is_4x:
            relevant.append((weakness, count, is_4x))

    if not relevant:
        relevant = [
            (weakness, count, False)
            for weakness, count in sorted(weakness_count.items(), key=lambda item: (-item[1], item[0]))[:3]
        ]

    return sorted(relevant, key=lambda item: (-(item[1]), 0 if item[2] else 1, item[0]))[:4]


def get_candidate_pokemon(limit=75):
    """Fetch a list of Pokémon names dynamically from the PokeAPI."""
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon?limit={limit}", timeout=10)
    response.raise_for_status()
    data = response.json()
    return [entry["name"] for entry in data["results"]]


def score_replacement(candidate_name, weakness_count, four_x_weakness_count, resistance_count):
    """Score how well a candidate Pokémon would balance the team’s biggest weaknesses and resistances."""
    try:
        candidate_multipliers = get_pokemon_multipliers(candidate_name)
    except requests.RequestException:
        return None

    relevant_weaknesses = get_relevant_weaknesses(weakness_count, four_x_weakness_count)
    score = 0
    improved_against = []
    reduced_resistance = []

    for weakness, count, is_4x in relevant_weaknesses:
        multiplier = candidate_multipliers.get(weakness, 1)
        weight = 2 if is_4x else 1
        if multiplier in (0.5, 0):
            score += count * weight
            improved_against.append(weakness)
        elif multiplier in (2, 4):
            score -= count * weight
            reduced_resistance.append(weakness)

    for resistance, count in resistance_count.items():
        multiplier = candidate_multipliers.get(resistance, 1)
        if multiplier in (2, 4):
            score -= count
            reduced_resistance.append(resistance)
        elif multiplier in (0.5, 0):
            score += count
            improved_against.append(resistance)

    if score <= 0:
        return None

    return score, improved_against, reduced_resistance


def recommend_replacements(team_members, weakness_count, four_x_weakness_count, resistance_count, limit=5):
    """Recommend a swap that helps balance the team’s shared weaknesses and resistances."""
    existing = {member["name"].lower() for member in team_members}
    scored = []

    for candidate in get_candidate_pokemon(limit=max(limit * 3, 75)):
        if candidate.lower() in existing:
            continue
        result = score_replacement(candidate, weakness_count, four_x_weakness_count, resistance_count)
        if result is None:
            continue
        score, improved_against, _ = result
        if score > 0:
            scored.append((score, candidate, improved_against))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[:limit]


def main():
    weakness_count = {}
    four_x_weakness_count = {}
    weakness_contributors = {}
    resistance_count = {}
    resistance_contributors = {}
    team = []
    team_members = []

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
            resistance_count,
            resistance_contributors,
        )
        team.append(format_name(name))
        team_members.append(
            {
                "name": format_name(name),
                "weaknesses": {
                    attack_type: multiplier
                    for attack_type, multiplier in multipliers.items()
                    if multiplier in (2, 4)
                },
            }
        )

    print("Team:", team)
    print("Weakness count:")
    for weakness, count in sorted(weakness_count.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {weakness}: {count}")

    print("\n4x weakness count:")
    for weakness, count in sorted(four_x_weakness_count.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {weakness}: {count}")

    print("\nSuggested defensive types:")
    for weakness, count, _ in get_relevant_weaknesses(weakness_count, four_x_weakness_count):
        suggestions = get_defensive_type_suggestions(weakness)
        print(f"  {weakness} ({count} Pokémon): consider adding {format_suggestion(suggestions)}")

    print("\nSuggested swaps:")
    replacements = recommend_replacements(
        team_members,
        weakness_count,
        four_x_weakness_count,
        resistance_count,
    )
    if not replacements:
        print("  None found")
    else:
        for score, candidate, improved_against in replacements:
            print(
                f"  {format_name(candidate)} (score {score}): helps balance {', '.join(improved_against)}"
            )

    print("\nWeakness contributors:")
    for weakness, contributors in sorted(weakness_contributors.items(), key=lambda item: item[0]):
        print(f"  {weakness}: {contributors}")

    print("\nResistance count:")
    for resistance, count in sorted(resistance_count.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {resistance}: {count}")

    print("\nResistance contributors:")
    for resistance, contributors in sorted(resistance_contributors.items(), key=lambda item: item[0]):
        print(f"  {resistance}: {contributors}")


if __name__ == "__main__":
    main()