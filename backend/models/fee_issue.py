from pydantic import BaseModel

class FeeIssue(BaseModel):
    fee_name: str
    related_review_count: int
    share_of_corpus: float
    representative_complaints: list[str]
    observed_misunderstanding: str
    confidence: str                     # High / Medium / Low
    selection_reason: str

class OfficialSource(BaseModel):
    url: str
    title: str
    domain: str
    extracted_info: str
    date_checked: str
