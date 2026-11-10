import requests

TYPE_CACHE = {}
POKEMON_MULTIPLIER_CACHE = {}
POKEMON_STATS_CACHE = {}


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

        elif multiplier < 1:
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


def get_candidate_pokemon(limit=1000):
    """Fetch a list of Pokémon names dynamically from the PokeAPI."""
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon?limit={limit}", timeout=10)
    response.raise_for_status()
    data = response.json()
    return [entry["name"] for entry in data["results"]]


def get_pokemon_stats(pokemon_name):
    """Fetch base stats for a Pokémon from the PokeAPI."""
    normalized_name = pokemon_name.strip().lower()
    if normalized_name in POKEMON_STATS_CACHE:
        return POKEMON_STATS_CACHE[normalized_name]

    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{normalized_name}", timeout=10)
    response.raise_for_status()
    data = response.json()
    total_stats = sum(stat["base_stat"] for stat in data["stats"])
    POKEMON_STATS_CACHE[normalized_name] = total_stats
    return total_stats


def summarize_team_counts(team_members):
    """Return weakness, 4x weakness, and resistance counts for a team."""
    weakness_count = {}
    four_x_weakness_count = {}
    resistance_count = {}

    for member in team_members:
        for attack_type, multiplier in member["multipliers"].items():
            if multiplier == 2:
                weakness_count[attack_type] = weakness_count.get(attack_type, 0) + 1
            elif multiplier == 4:
                weakness_count[attack_type] = weakness_count.get(attack_type, 0) + 1
                four_x_weakness_count[attack_type] = four_x_weakness_count.get(attack_type, 0) + 1
            elif multiplier < 1:
                resistance_count[attack_type] = resistance_count.get(attack_type, 0) + 1

    return weakness_count, four_x_weakness_count, resistance_count


def score_swap(
    candidate_name,
    swap_out_name,
    team_members,
    weakness_count,
    four_x_weakness_count,
    resistance_count,
    candidate_bst,
):
    """Score a candidate swap by comparing the team’s balance before and after the swap."""
    try:
        candidate_multipliers = get_pokemon_multipliers(candidate_name)
    except requests.RequestException:
        return None

    replaced_team = [member for member in team_members if member["name"].lower() != swap_out_name.lower()]
    replaced_team.append(
        {
            "name": format_name(candidate_name),
            "multipliers": candidate_multipliers,
        }
    )

    hypothetical_weakness_count, hypothetical_four_x_weakness_count, hypothetical_resistance_count = summarize_team_counts(
        replaced_team
    )

    score = 0
    improved_against = []

    all_types = set(weakness_count) | set(resistance_count) | set(hypothetical_weakness_count) | set(
        hypothetical_resistance_count
    )
    for attack_type in sorted(all_types):
        current_weak = weakness_count.get(attack_type, 0)
        current_resistance = resistance_count.get(attack_type, 0)
        new_weak = hypothetical_weakness_count.get(attack_type, 0)
        new_resistance = hypothetical_resistance_count.get(attack_type, 0)
        weak_weight = 2 if four_x_weakness_count.get(attack_type, 0) > 0 else 1
        score += (current_weak - new_weak) * weak_weight
        score += (new_resistance - current_resistance)

        if new_weak < current_weak or new_resistance > current_resistance:
            improved_against.append(attack_type)

    score += candidate_bst / 80

    if score <= 0:
        return None

    return score, improved_against[:5]


def recommend_replacements(team_members, weakness_count, four_x_weakness_count, resistance_count, limit=5):
    """Recommend swaps that improve the team’s weakness/resistance balance."""
    existing = {member["name"].lower() for member in team_members}
    scored = []

    candidates = get_candidate_pokemon(limit=1000)
    scored_candidates = []
    for candidate in candidates:
        if candidate.lower() in existing:
            continue
        try:
            total_stats = get_pokemon_stats(candidate)
        except requests.RequestException:
            continue
        if total_stats < 440 or total_stats > 560:
            continue
        scored_candidates.append((total_stats, candidate))

    scored_candidates.sort(key=lambda item: (-item[0], item[1]))

    for _, candidate in scored_candidates:
        for member in team_members:
            result = score_swap(
                candidate,
                member["name"],
                team_members,
                weakness_count,
                four_x_weakness_count,
                resistance_count,
                get_pokemon_stats(candidate),
            )
            if result is None:
                continue
            score, improved_against = result
            if score > 0:
                scored.append((score, candidate, member["name"], improved_against))

    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
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
                "multipliers": multipliers,
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
        best_score, best_candidate, best_member, best_improvements = replacements[0]
        print(
            f"  Best swap: replace {best_member} with {format_name(best_candidate)} (score {best_score})"
        )
        print(f"    Improves: {', '.join(best_improvements)}")

        for score, candidate, member, improved_against in replacements[1:]:
            print(
                f"  Replace {member} with {format_name(candidate)} (score {score}): {', '.join(improved_against)}"
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