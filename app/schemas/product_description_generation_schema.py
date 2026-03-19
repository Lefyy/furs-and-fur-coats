from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductDescriptionGenerationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    status: str
    generated_text: str | None
    model_name: str | None
    prompt_version: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None