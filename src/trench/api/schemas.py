from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from trench.domain.enums import Conference, Division


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=64)
    abbreviation: str = Field(pattern=r"^[A-Z]{2,4}$")
    conference: Conference
    division: Division


class TeamRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    abbreviation: str
    conference: Conference
    division: Division
