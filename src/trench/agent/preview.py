import re

from pydantic_ai import Agent, AgentRunError, ModelRetry, RunContext
from pydantic_ai.models import Model

from trench.application.previews import (
    MatchupContext,
    MatchupPreview,
    PreviewUnavailableError,
)

PERCENTAGE = re.compile(r"(\d{1,3})(?:[.,]\d+)?\s?%")
PERCENT_TOLERANCE = 1

STAT_KEYWORD = (
    r"(?:jardas?|yards?|touchdowns?|tds?|sacks?|interceptaç\w*|turnovers?"
    r"|vit[oó]rias?|derrotas?|retrospecto|wins?|losses?|record"
    r"|placar|pontos?|points?|score)"
)
NUMBER = r"\d+(?:[.,]\d+)?"
NUMBER_NEAR_STAT_KEYWORD = re.compile(
    rf"(?:({NUMBER})\s*{STAT_KEYWORD})|(?:{STAT_KEYWORD}\s*(?:de\s*)?({NUMBER}))",
    re.IGNORECASE,
)
NUMBER_TOLERANCE = 0.5

INSTRUCTIONS = """
You are Trench, an NFL analyst writing a short matchup preview.
Write every field in {language}.

The user message is a JSON document with everything computed by Trench's
statistical model for the current season. It is your only source of facts:
- Never invent statistics, injuries, players, records or storylines.
- When you mention a win probability, quote win_probability_pct exactly.
- Projected points, spread and averages must come from the context.
- Any yardage, touchdown, sack, interception or turnover number you cite
  must match a value already present in the context.
- If a team has played two games or fewer, say the sample is still small.
- Absences with a negative points_delta hurt that team's own scoring; a
  positive one helps the opponent.
- players_to_watch may only name players listed in absences or leaders.
- If "outcome" is present, the game has already been played: write a recap
  instead of a preview, and state the final score from outcome exactly.
  If outcome.was_upset is true, say plainly that the winner was not the
  pre-game favorite (an upset/zebra). If false, explain the favorite won
  as the numbers suggested, using the opponent's rating and record for
  context on why the result was not surprising.
""".strip()


def _preview_text(preview: MatchupPreview) -> str:
    return " ".join(
        [
            preview.headline,
            preview.summary,
            *preview.key_factors,
            *preview.players_to_watch,
        ]
    )


def ungrounded_percentages(
    preview: MatchupPreview, context: MatchupContext
) -> set[int]:
    quoted = {int(match) for match in PERCENTAGE.findall(_preview_text(preview))}
    return {
        value
        for value in quoted
        if all(
            abs(value - allowed) > PERCENT_TOLERANCE
            for allowed in context.win_probabilities_pct
        )
    }


def _context_stat_numbers(context: MatchupContext) -> set[float]:
    values = {
        context.spread,
        context.home.points_for_avg,
        context.home.points_against_avg,
        context.home.projected_points,
        context.home.turnover_margin,
        context.away.points_for_avg,
        context.away.points_against_avg,
        context.away.projected_points,
        context.away.turnover_margin,
    }
    for team in (context.home, context.away):
        if team.yards_per_play is not None:
            values.add(team.yards_per_play)
        if team.yards_per_play_allowed is not None:
            values.add(team.yards_per_play_allowed)
        values.update({team.wins, team.losses, team.ties})
    for absence in context.absences:
        values.add(absence.points_delta)
    for leader in context.leaders:
        values.add(leader.value)
    for quarterback in context.quarterbacks:
        values.update(
            {
                quarterback.passing_yards,
                quarterback.passing_touchdowns,
                quarterback.interceptions_thrown,
                quarterback.rushing_touchdowns,
            }
        )
    if context.outcome is not None:
        values.update({context.outcome.home_score, context.outcome.away_score})
    return values


def ungrounded_stat_numbers(
    preview: MatchupPreview, context: MatchupContext
) -> set[float]:
    text = _preview_text(preview)
    quoted = {
        float((match.group(1) or match.group(2)).replace(",", "."))
        for match in NUMBER_NEAR_STAT_KEYWORD.finditer(text)
    }
    allowed = _context_stat_numbers(context)
    return {
        value
        for value in quoted
        if all(
            abs(value - allowed_value) > NUMBER_TOLERANCE for allowed_value in allowed
        )
    }


def create_preview_agent(
    model: Model | str, *, language: str
) -> Agent[MatchupContext, MatchupPreview]:
    agent = Agent(
        model,
        deps_type=MatchupContext,
        output_type=MatchupPreview,
        instructions=INSTRUCTIONS.format(language=language),
        retries=2,
    )

    @agent.output_validator
    def grounded(
        ctx: RunContext[MatchupContext], preview: MatchupPreview
    ) -> MatchupPreview:
        unknown_percentages = ungrounded_percentages(preview, ctx.deps)
        if unknown_percentages:
            allowed = ", ".join(f"{p}%" for p in sorted(ctx.deps.win_probabilities_pct))
            raise ModelRetry(
                f"Percentages {sorted(unknown_percentages)} are not in the context. "
                f"Only quote the win probabilities {allowed}."
            )
        unknown_numbers = ungrounded_stat_numbers(preview, ctx.deps)
        if unknown_numbers:
            raise ModelRetry(
                f"Stat numbers {sorted(unknown_numbers)} are not in the context. "
                "Only quote yardage, touchdown, sack, interception or turnover "
                "numbers that appear in the JSON context."
            )
        return preview

    return agent


class AgentPreviewWriter:
    def __init__(self, agent: Agent[MatchupContext, MatchupPreview]) -> None:
        self._agent = agent

    async def write(self, context: MatchupContext) -> MatchupPreview:
        try:
            result = await self._agent.run(
                context.model_dump_json(indent=2), deps=context
            )
        except AgentRunError as error:
            raise PreviewUnavailableError(str(error)) from error
        return result.output
