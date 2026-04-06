from datetime import datetime
from typing import Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status, content=self.model_dump())


class TimestampSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
