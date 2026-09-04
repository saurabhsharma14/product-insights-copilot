from pydantic import BaseModel

class Theme(BaseModel):
    theme_name: str
    description: str
    review_count: int
    percentage: float
    negative_count: int
    avg_rating: float
    representative_review_ids: list[str]
    trend: str = "Stable"               # Increasing / Decreasing / Stable / Spiking
    rank_score: float = 0.0
