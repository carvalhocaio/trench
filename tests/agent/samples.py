from datetime import UTC, datetime

from trench.application.previews import MatchupContext, MatchupPreview, TeamFacts

CONTEXT = MatchupContext(
    season=2026,
    week=2,
    kickoff=datetime(2026, 9, 20, 20, 25, tzinfo=UTC),
    home=TeamFacts(
        name="Las Vegas Raiders",
        abbreviation="LV",
        games_played=1,
        wins=0,
        losses=1,
        ties=0,
        points_for_avg=17.5,
        points_against_avg=22.5,
        yards_per_play=5.1,
        yards_per_play_allowed=6.0,
        turnover_margin=-1.0,
        projected_points=16.2,
        win_probability_pct=27,
    ),
    away=TeamFacts(
        name="Kansas City Chiefs",
        abbreviation="KC",
        games_played=1,
        wins=1,
        losses=0,
        ties=0,
        points_for_avg=22.5,
        points_against_avg=17.5,
        yards_per_play=6.0,
        yards_per_play_allowed=5.1,
        turnover_margin=1.0,
        projected_points=24.5,
        win_probability_pct=73,
    ),
    spread=-8.3,
    absences=[],
    leaders=[],
    quarterbacks=[],
)

GROUNDED = MatchupPreview(
    headline="Chiefs chegam a Las Vegas com 73% de chance",
    summary="Amostra ainda pequena: cada time jogou apenas uma partida.",
    key_factors=["Ataque do KC acima da média", "Defesa do LV cedeu 22,5 pontos"],
)
