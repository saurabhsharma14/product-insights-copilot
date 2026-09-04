from pydantic import BaseModel
from .fee_issue import OfficialSource

class CustomerQuote(BaseModel):
    review_id: str
    quote: str
    date: str
    rating: int
    theme: str
    source: str = "Google Play"

class ProductPulse(BaseModel):
    content: str
    word_count: int
    top_themes_summary: str
    user_voice_quotes: list[CustomerQuote]
    key_observation: str
    product_actions: list[str]          # Exactly 3

class FeeExplainer(BaseModel):
    fee_name: str
    customer_confusion_summary: str
    bullets: list[str]                  # Max 6
    sources: list[OfficialSource]
    last_checked: str
