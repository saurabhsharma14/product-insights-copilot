import json
from pydantic import BaseModel
from typing import List, Optional
from agents.llm import analysis_llm
from agents.prompts.fee_detection import fee_detection_prompt_template
from agents.state import PipelineState
from models.fee_issue import FeeIssue

class FeeDetectionOutput(BaseModel):
    has_fee_issue: bool
    fee_name: Optional[str]
    observed_misunderstanding: Optional[str]
    confidence: Optional[str]
    selection_reason: Optional[str]
    representative_complaints: Optional[List[str]]

def detect_fee_node(state: PipelineState):
    reviews = state.get("classified_reviews", [])
    if not reviews:
        return {"fee_issue": None}

    # Filter to reviews that might relate to fees
    # e.g., issue_type == "Pricing/Fees" or primary_theme includes fee keywords
    fee_keywords = ["fee", "charge", "money", "deduct", "hidden", "amc", "dp"]
    fee_reviews = [
        r for r in reviews 
        if r.issue_type == "Pricing/Fees" or 
        any(k in (r.primary_theme or "").lower() for k in fee_keywords) or
        any(k in r.review_text.lower() for k in fee_keywords)
    ]
    
    # If no fee reviews, fallback to sending a sample of negative reviews
    if not fee_reviews:
        fee_reviews = [r for r in reviews if r.sentiment == "Negative"]
        
    reviews_data = [
        {
            "review_id": r.review_id,
            "review_text": r.review_text,
            "rating": r.rating,
        } 
        for r in fee_reviews
    ]
    
    reviews_json = json.dumps(reviews_data[:100], ensure_ascii=False) # cap at 100
    
    prompt = fee_detection_prompt_template.invoke({"reviews_json": reviews_json})
    
    llm_with_structure = analysis_llm.with_structured_output(FeeDetectionOutput, method="json_mode")
    
    try:
        result = llm_with_structure.invoke(prompt)
        
        if result.has_fee_issue and result.fee_name:
            fee_issue = FeeIssue(
                fee_name=result.fee_name,
                related_review_count=len(fee_reviews),
                share_of_corpus=round((len(fee_reviews) / len(reviews) * 100) if reviews else 0, 2),
                representative_complaints=result.representative_complaints or [],
                observed_misunderstanding=result.observed_misunderstanding or "",
                confidence=result.confidence or "Medium",
                selection_reason=result.selection_reason or ""
            )
            return {"fee_issue": fee_issue}
    except Exception as e:
        print(f"Fee detection failed: {e}")
        
    return {"fee_issue": None}
