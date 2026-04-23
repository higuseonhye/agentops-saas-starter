from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    q: str = Field(min_length=1)


class ReplayRequest(BaseModel):
    id: str


class UsageResponse(BaseModel):
    total_cost: float
    total_requests: int
    total_tokens: int
    daily_cost: list[float]


class PerformanceResponse(BaseModel):
    accuracy: float
    retrieval: float
    generation: float
