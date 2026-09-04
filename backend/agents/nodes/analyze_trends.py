from datetime import datetime
from agents.state import PipelineState

def analyze_trends_node(state: PipelineState):
    themes = state.get("themes", [])
    reviews = state.get("classified_reviews", [])
    
    if not themes or not reviews:
        return {"themes": themes}
        
    # Simple trend calculation: compare first half of dates to second half
    # Let's find min and max dates
    dates = []
    for r in reviews:
        try:
            # handle formats like ISO 8601
            d = datetime.fromisoformat(r.review_date.replace('Z', '+00:00'))
            dates.append(d)
        except:
            pass
            
    if not dates:
        return {"themes": themes}
        
    min_date = min(dates)
    max_date = max(dates)
    mid_point = min_date + (max_date - min_date) / 2
    
    # Pre-calculate review halves
    first_half_reviews = set(r.review_id for r in reviews if datetime.fromisoformat(r.review_date.replace('Z', '+00:00')) < mid_point)
    second_half_reviews = set(r.review_id for r in reviews if datetime.fromisoformat(r.review_date.replace('Z', '+00:00')) >= mid_point)
    
    for theme in themes:
        # Get reviews matching theme
        theme_reviews = [r for r in reviews if theme.theme_name.lower() in (r.primary_theme or "").lower()]
        
        # fallback
        if not theme_reviews:
            theme_reviews = [r for r in reviews if r.review_id in theme.representative_review_ids]
            
        first_half_count = sum(1 for r in theme_reviews if r.review_id in first_half_reviews)
        second_half_count = sum(1 for r in theme_reviews if r.review_id in second_half_reviews)
        
        if first_half_count == 0 and second_half_count > 0:
            trend = "Spiking"
        elif second_half_count > first_half_count * 1.5:
            trend = "Increasing"
        elif first_half_count > second_half_count * 1.5:
            trend = "Decreasing"
        else:
            trend = "Stable"
            
        theme.trend = trend

    return {"themes": themes}
