from collections import Counter

from trench.domain.league import NFL_FRANCHISES


def test_league_has_32_unique_franchises() -> None:
    abbreviations = [franchise.abbreviation for franchise in NFL_FRANCHISES]

    assert len(NFL_FRANCHISES) == 32
    assert len(set(abbreviations)) == 32
    assert all(abbreviation.isupper() for abbreviation in abbreviations)


def test_every_division_has_four_teams() -> None:
    divisions = Counter((f.conference, f.division) for f in NFL_FRANCHISES)

    assert len(divisions) == 8
    assert set(divisions.values()) == {4}
