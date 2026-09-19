import pytest
from sqlalchemy import Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from trench.infrastructure.models import Base

TABLES = list(Base.metadata.sorted_tables)


@pytest.mark.parametrize("table", TABLES, ids=lambda table: table.name)
def test_table_compiles_for_postgres(table: Table) -> None:
    ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))

    assert f"CREATE TABLE {table.name}" in ddl


@pytest.mark.parametrize("table", TABLES, ids=lambda table: table.name)
def test_every_constraint_is_named(table: Table) -> None:
    unnamed = [type(c).__name__ for c in table.constraints if not c.name]

    assert unnamed == []


def test_timestamps_are_timezone_aware() -> None:
    kickoff = Base.metadata.tables["games"].c.kickoff

    assert kickoff.type.timezone is True
