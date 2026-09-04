from agents.state import PipelineState

def rank_themes_node(state: PipelineState):
    themes = state.get("themes", [])
    if not themes:
        return {"themes": []}
        
    for theme in themes:
        # Calculate frequency score (normalized percentage)
        freq_score = min(theme.percentage / 100.0, 1.0)
        
        # Calculate negativity score (ratio of negative reviews)
        neg_ratio = theme.negative_count / theme.review_count if theme.review_count > 0 else 0
        neg_score = neg_ratio
        
        # Severity score (placeholder, could compute from reviews in this theme)
        severity_score = 0.5 # Default medium severity for now
        
        # Recency score (placeholder, could compute from review dates)
        recency_score = 0.5
        
        # Persistence score (placeholder)
        persistence_score = 0.5
        
        # Score = 0.30×Frequency + 0.25×Negativity + 0.20×Severity + 0.15×Recency + 0.10×Persistence
        score = (0.30 * freq_score) + (0.25 * neg_score) + (0.20 * severity_score) + (0.15 * recency_score) + (0.10 * persistence_score)
        
        theme.rank_score = round(score, 4)
        
    # Sort themes by rank_score descending
    sorted_themes = sorted(themes, key=lambda x: x.rank_score, reverse=True)
    
    # Keep top 3
    top_themes = sorted_themes[:3]
    
    return {"themes": top_themes}
