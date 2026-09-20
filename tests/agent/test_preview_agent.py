import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from tests.agent.samples import CONTEXT, GROUNDED
from trench.agent.preview import (
    AgentPreviewWriter,
    create_preview_agent,
    ungrounded_percentages,
    ungrounded_stat_numbers,
)
from trench.application.previews import MatchupPreview, PreviewUnavailableError

INVENTED = GROUNDED.model_copy(
    update={"headline": "Chiefs têm 91% de chance em Las Vegas"}
)
INVENTED_YARDS = GROUNDED.model_copy(
    update={"summary": "Ataque com 999 jardas por jogo nesta temporada."}
)


def scripted(*previews: MatchupPreview) -> tuple[FunctionModel, list[int]]:
    calls: list[int] = []

    def respond(_: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        preview = previews[min(len(calls), len(previews) - 1)]
        calls.append(len(calls))
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name=info.output_tools[0].name, args=preview.model_dump()
                )
            ]
        )

    return FunctionModel(respond), calls


def writer_for(model: FunctionModel) -> AgentPreviewWriter:
    return AgentPreviewWriter(create_preview_agent(model, language="pt-BR"))


async def test_accepts_grounded_preview() -> None:
    model, calls = scripted(GROUNDED)

    preview = await writer_for(model).write(CONTEXT)

    assert preview == GROUNDED
    assert len(calls) == 1


async def test_retries_when_probability_is_invented() -> None:
    model, calls = scripted(INVENTED, GROUNDED)

    preview = await writer_for(model).write(CONTEXT)

    assert preview == GROUNDED
    assert len(calls) == 2


async def test_gives_up_after_repeated_invention() -> None:
    model, _ = scripted(INVENTED)

    with pytest.raises(PreviewUnavailableError):
        await writer_for(model).write(CONTEXT)


async def test_retries_when_a_stat_number_is_invented() -> None:
    model, calls = scripted(INVENTED_YARDS, GROUNDED)

    preview = await writer_for(model).write(CONTEXT)

    assert preview == GROUNDED
    assert len(calls) == 2


async def test_gives_up_after_repeated_stat_invention() -> None:
    model, _ = scripted(INVENTED_YARDS)

    with pytest.raises(PreviewUnavailableError):
        await writer_for(model).write(CONTEXT)


async def test_instructions_carry_the_language() -> None:
    seen: list[str | None] = []

    def respond(_: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info.instructions)
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name=info.output_tools[0].name, args=GROUNDED.model_dump()
                )
            ]
        )

    agent = create_preview_agent(FunctionModel(respond), language="en-US")
    await AgentPreviewWriter(agent).write(CONTEXT)

    assert seen[0] is not None
    assert "en-US" in seen[0]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("73% para o KC", set()),
        ("cerca de 72%", set()),
        ("27 % para o LV", set()),
        ("91% de chance", {91}),
        ("sem percentuais", set()),
    ],
)
def test_ungrounded_percentages(text: str, expected: set[int]) -> None:
    preview = GROUNDED.model_copy(update={"summary": text})

    assert ungrounded_percentages(preview, CONTEXT) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ataque com 6 jardas por jogada", set()),
        ("defesa cede 5,1 jardas por jogada", set()),
        ("ataque com 999 jardas por jogo", {999.0}),
        ("defesa fez 2 interceptações na temporada", {2.0}),
        ("chegam com retrospecto de 1 vitória", set()),
        ("chegam com retrospecto de 9 vitórias", {9.0}),
        ("na semana 5 o time folgou", set()),
        ("sem números de estatística aqui", set()),
    ],
)
def test_ungrounded_stat_numbers(text: str, expected: set[float]) -> None:
    preview = GROUNDED.model_copy(update={"summary": text})

    assert ungrounded_stat_numbers(preview, CONTEXT) == expected
