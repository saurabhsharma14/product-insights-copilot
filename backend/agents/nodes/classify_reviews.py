import json
from pydantic import BaseModel, Field
from typing import List, Optional
from agents.llm import analysis_llm
from agents.prompts.classify import classify_prompt_template
from agents.state import PipelineState
from models.review import ReviewRecord

class ClassifiedReviewOutput(BaseModel):
    review_id: str
    primary_theme: str
    secondary_theme: Optional[str]
    sentiment: str
    severity: str
    issue_type: Optional[str]

class ClassificationBatchOutput(BaseModel):
    classifications: List[ClassifiedReviewOutput]

def classify_reviews_node(state: PipelineState):
    reviews = state.get("reviews", [])
    if not reviews:
        return {"classified_reviews": []}
        
    classified_reviews = []
    
    # Process in chunks of 50
    chunk_size = 50
    
    llm_with_structure = analysis_llm.with_structured_output(ClassificationBatchOutput, method="json_mode")
    
    for i in range(0, len(reviews), chunk_size):
        chunk = reviews[i:i + chunk_size]
        
        # Prepare JSON string of reviews for the prompt
        reviews_data = [
            {
                "review_id": r.review_id, 
                "review_text": r.review_text,
                "rating": r.rating
            } 
            for r in chunk
        ]
        reviews_json = json.dumps(reviews_data, ensure_ascii=False)
        
        prompt = classify_prompt_template.invoke({"reviews_json": reviews_json})
        
        try:
            result = llm_with_structure.invoke(prompt)
            # Map back to ReviewRecord
            classifications_map = {c.review_id: c for c in result.classifications}
            
            for r in chunk:
                c = classifications_map.get(r.review_id)
                if c:
                    r.primary_theme = c.primary_theme
                    r.secondary_theme = c.secondary_theme
                    r.sentiment = c.sentiment
                    r.severity = c.severity
                    r.issue_type = c.issue_type
                classified_reviews.append(r)
        except Exception as e:
            # Fallback on error: keep original reviews unclassified
            print(f"Classification failed for chunk {i}: {e}")
            for r in chunk:
                classified_reviews.append(r)
                
    return {"classified_reviews": classified_reviews}
