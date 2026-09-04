from pydantic import BaseModel
from typing import Optional

class ReviewRecord(BaseModel):
    review_id: str
    review_text: str
    rating: int                        # 1-5
    review_date: str                   # ISO 8601
    app_version: str = ""
    developer_reply: str = ""
    source: str = "Google Play"
    source_url: str = ""
    # Classification (populated after analysis)
    primary_theme: Optional[str] = None
    secondary_theme: Optional[str] = None
    sentiment: Optional[str] = None     # Positive / Neutral / Negative
    severity: Optional[str] = None
    issue_type: Optional[str] = None
