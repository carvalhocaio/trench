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
