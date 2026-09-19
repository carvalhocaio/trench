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

INSTRUCTIONS = """
You are Trench, an NFL analyst writing a short matchup preview.
Write every field in {language}.

The user message is a JSON document with everything computed by Trench's
statistical model for the current season. It is your only source of facts:
- Never invent statistics, injuries, players, records or storylines.
- When you mention a win probability, quote win_probability_pct exactly.
- Projected points, spread and averages must come from the context.
- If a team has played two games or fewer, say the sample is still small.
- Absences with a negative points_delta hurt that team's own scoring; a
  positive one helps the opponent.
- players_to_watch may only name players listed in absences or leaders.
""".strip()


def ungrounded_percentages(
    preview: MatchupPreview, context: MatchupContext
) -> set[int]:
    text = " ".join(
        [
            preview.headline,
            preview.summary,
            *preview.key_factors,
            *preview.players_to_watch,
        ]
    )
    quoted = {int(match) for match in PERCENTAGE.findall(text)}
    return {
        value
        for value in quoted
        if all(
            abs(value - allowed) > PERCENT_TOLERANCE
            for allowed in context.win_probabilities_pct
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
        unknown = ungrounded_percentages(preview, ctx.deps)
        if unknown:
            allowed = ", ".join(f"{p}%" for p in sorted(ctx.deps.win_probabilities_pct))
            raise ModelRetry(
                f"Percentages {sorted(unknown)} are not in the context. "
                f"Only quote the win probabilities {allowed}."
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
