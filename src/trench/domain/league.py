from dataclasses import dataclass

from trench.domain.enums import Conference, Division


@dataclass(frozen=True, slots=True)
class Franchise:
    name: str
    abbreviation: str
    conference: Conference
    division: Division


def _division(
    conference: Conference, division: Division, *teams: tuple[str, str]
) -> tuple[Franchise, ...]:
    return tuple(
        Franchise(name, abbreviation, conference, division)
        for name, abbreviation in teams
    )


NFL_FRANCHISES: tuple[Franchise, ...] = (
    *_division(
        Conference.AFC,
        Division.EAST,
        ("Buffalo Bills", "BUF"),
        ("Miami Dolphins", "MIA"),
        ("New England Patriots", "NE"),
        ("New York Jets", "NYJ"),
    ),
    *_division(
        Conference.AFC,
        Division.NORTH,
        ("Baltimore Ravens", "BAL"),
        ("Cincinnati Bengals", "CIN"),
        ("Cleveland Browns", "CLE"),
        ("Pittsburgh Steelers", "PIT"),
    ),
    *_division(
        Conference.AFC,
        Division.SOUTH,
        ("Houston Texans", "HOU"),
        ("Indianapolis Colts", "IND"),
        ("Jacksonville Jaguars", "JAX"),
        ("Tennessee Titans", "TEN"),
    ),
    *_division(
        Conference.AFC,
        Division.WEST,
        ("Denver Broncos", "DEN"),
        ("Kansas City Chiefs", "KC"),
        ("Las Vegas Raiders", "LV"),
        ("Los Angeles Chargers", "LAC"),
    ),
    *_division(
        Conference.NFC,
        Division.EAST,
        ("Dallas Cowboys", "DAL"),
        ("New York Giants", "NYG"),
        ("Philadelphia Eagles", "PHI"),
        ("Washington Commanders", "WAS"),
    ),
    *_division(
        Conference.NFC,
        Division.NORTH,
        ("Chicago Bears", "CHI"),
        ("Detroit Lions", "DET"),
        ("Green Bay Packers", "GB"),
        ("Minnesota Vikings", "MIN"),
    ),
    *_division(
        Conference.NFC,
        Division.SOUTH,
        ("Atlanta Falcons", "ATL"),
        ("Carolina Panthers", "CAR"),
        ("New Orleans Saints", "NO"),
        ("Tampa Bay Buccaneers", "TB"),
    ),
    *_division(
        Conference.NFC,
        Division.WEST,
        ("Arizona Cardinals", "ARI"),
        ("Los Angeles Rams", "LAR"),
        ("San Francisco 49ers", "SF"),
        ("Seattle Seahawks", "SEA"),
    ),
)
