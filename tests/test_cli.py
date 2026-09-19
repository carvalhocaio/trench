import json

import pytest

from trench.cli import main


def test_openapi_prints_the_api_schema(capsys: pytest.CaptureFixture[str]) -> None:
    main(["openapi"])

    schema = json.loads(capsys.readouterr().out)
    assert schema["info"]["title"] == "Trench"
    assert "/games/{game_id}/prediction" in schema["paths"]


def test_rejects_unknown_command() -> None:
    with pytest.raises(SystemExit):
        main(["unknown"])


def test_import_schedule_requires_a_season() -> None:
    with pytest.raises(SystemExit):
        main(["import-schedule"])


def test_import_injuries_requires_a_season_and_week() -> None:
    with pytest.raises(SystemExit):
        main(["import-injuries", "--season", "2026"])


def test_import_stats_requires_a_season_and_week() -> None:
    with pytest.raises(SystemExit):
        main(["import-stats", "--week", "2"])
