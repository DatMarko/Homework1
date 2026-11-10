from team_builder import format_suggestion, summarize_team_counts


def test_format_suggestion_with_no_types():
    assert format_suggestion([]) == "no obvious defensive type"
    
def test_quarter_damage_counts_as_resistance():
    # Arrange: a team with one Pokémon that takes 0.25x damage from normal
    team = [{"name": "Steelix", "multipliers": {"normal": 0.25}}]

    # Act
    weakness_count, four_x_weakness_count, resistance_count = summarize_team_counts(team)

    # Assert
    assert resistance_count == {"normal": 1}

def test_format_suggestion_with_one_type():
    assert format_suggestion(["fire"]) == "a fire type"


def test_format_suggestion_with_two_types():
    assert format_suggestion(["fire", "water"]) == "a fire or water type"


def test_format_suggestion_with_three_types():
    assert format_suggestion(["fire", "water", "grass"]) == "a fire, water, or grass type"


def test_format_suggestion_with_more_than_five_types_shows_only_five():
    types = ["bug", "dark", "dragon", "electric", "fairy", "fighting", "fire"]
    assert format_suggestion(types) == "a bug, dark, dragon, electric, or fairy type"
