from typing import TypedDict, Optional
from models.review import ReviewRecord
from models.theme import Theme
from models.fee_issue import FeeIssue, OfficialSource
from models.outputs import ProductPulse, FeeExplainer, CustomerQuote

class PipelineState(TypedDict):
    batch_id: str
    reviews: list[ReviewRecord]
    classified_reviews: list[ReviewRecord]
    themes: list[Theme]
    fee_issue: Optional[FeeIssue]
    official_sources: list[OfficialSource]
    product_pulse: Optional[ProductPulse]
    fee_explainer: Optional[FeeExplainer]
    quotes: list[CustomerQuote]
    analysis_status: str
