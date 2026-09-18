from pydantic import BaseModel, ConfigDict


class APIResponse(BaseModel):
    success: bool = True
    message: str
    data: object | None = None


class Meta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ListResponse(BaseModel):
    success: bool = True
    data: list
    meta: Meta


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
