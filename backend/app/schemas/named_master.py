from pydantic import BaseModel, ConfigDict, Field


class NamedMasterWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class NamedMasterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
