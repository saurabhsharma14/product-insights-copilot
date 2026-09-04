import json
from pydantic import BaseModel
from typing import List
from agents.llm import analysis_llm
from agents.prompts.cluster import cluster_prompt_template
from agents.state import PipelineState
from models.theme import Theme

class ThemeOutput(BaseModel):
    theme_name: str
    description: str
    representative_review_ids: List[str]

class ClusterBatchOutput(BaseModel):
    themes: List[ThemeOutput]

def cluster_themes_node(state: PipelineState):
    reviews = state.get("classified_reviews", [])
    if not reviews:
        return {"themes": []}

    # Prepare JSON string of reviews for the prompt
    # To avoid exceeding token limits, we might only send a sample or aggregate
    # But for now, we'll send a subset if too large, or just primary themes.
    # Let's send review_id, review_text, rating, primary_theme
    
    reviews_data = [
        {
            "review_id": r.review_id,
            "review_text": r.review_text,
            "rating": r.rating,
            "primary_theme": r.primary_theme,
            "sentiment": r.sentiment,
            "severity": r.severity
        } 
        for r in reviews
    ]
    
    # If the list is extremely long, we might need to truncate or chunk.
    # We will assume it fits in the LLM window (4096 tokens max for prompt is tight, 
    # but we are using 70b which likely has a larger context window).
    
    reviews_json = json.dumps(reviews_data[:200], ensure_ascii=False) # cap at 200 reviews for context
    
    prompt = cluster_prompt_template.invoke({"reviews_json": reviews_json})
    
    llm_with_structure = analysis_llm.with_structured_output(ClusterBatchOutput, method="json_mode")
    
    themes = []
    
    try:
        result = llm_with_structure.invoke(prompt)
        total_reviews = len(reviews)
        
        for t in result.themes:
            # Calculate stats for this theme. 
            # We match reviews that have this primary_theme, or we could just do a naive matching.
            # A better approach: The LLM didn't return which reviews belong to the theme except representative ones.
            # We will assign reviews to themes based on primary_theme string similarity or just exact match.
            # For simplicity, we count reviews whose primary_theme is similar, or we just rely on LLM for grouping.
            # Let's just group by exact match of `primary_theme` from classification phase to the clustered theme_name.
            # Actually, to make it robust, we can just find reviews containing the theme name in their primary_theme,
            # or we calculate stats based on the subset of reviews that match.
            
            # Since clustering is abstract, we might just assign reviews to the closest theme,
            # but here we'll do a simple substring match for counting, or fallback to 1 if 0.
            
            theme_reviews = [r for r in reviews if t.theme_name.lower() in (r.primary_theme or "").lower()]
            if not theme_reviews:
                # Fallback: just use all reviews with same severity or something, or randomly assign for demo
                theme_reviews = [r for r in reviews if r.review_id in t.representative_review_ids]
            
            review_count = len(theme_reviews)
            percentage = (review_count / total_reviews * 100) if total_reviews > 0 else 0
            negative_count = len([r for r in theme_reviews if r.sentiment == "Negative"])
            avg_rating = sum(r.rating for r in theme_reviews) / review_count if review_count > 0 else 0
            
            theme_obj = Theme(
                theme_name=t.theme_name,
                description=t.description,
                review_count=review_count,
                percentage=round(percentage, 2),
                negative_count=negative_count,
                avg_rating=round(avg_rating, 2),
                representative_review_ids=t.representative_review_ids,
                trend="Stable", # Default, updated in analyze_trends
                rank_score=0.0
            )
            themes.append(theme_obj)
    except Exception as e:
        print(f"Clustering failed: {e}")
        
    return {"themes": themes}
