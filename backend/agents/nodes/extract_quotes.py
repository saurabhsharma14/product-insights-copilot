from agents.state import PipelineState
from models.outputs import CustomerQuote

def extract_quotes_node(state: PipelineState):
    themes = state.get("themes", [])
    reviews = state.get("classified_reviews", [])
    
    if not themes or not reviews:
        return {"quotes": []}
        
    reviews_by_id = {r.review_id: r for r in reviews}
    quotes = []
    
    # Pick one representative quote from each of the top themes, up to 3 total quotes
    for theme in themes:
        if len(quotes) >= 3:
            break
            
        for rev_id in theme.representative_review_ids:
            r = reviews_by_id.get(rev_id)
            if r:
                # Verify we don't have this review already
                if not any(q.review_id == r.review_id for q in quotes):
                    quote = CustomerQuote(
                        review_id=r.review_id,
                        quote=r.review_text,
                        date=r.review_date,
                        rating=r.rating,
                        theme=theme.theme_name,
                        source=r.source
                    )
                    quotes.append(quote)
                    break # One per theme
                    
    # If we still need quotes, just take from the top negative reviews
    if len(quotes) < 3:
        negative_reviews = [r for r in reviews if r.sentiment == "Negative" and not any(q.review_id == r.review_id for q in quotes)]
        for r in negative_reviews:
            if len(quotes) >= 3:
                break
            quote = CustomerQuote(
                review_id=r.review_id,
                quote=r.review_text,
                date=r.review_date,
                rating=r.rating,
                theme=r.primary_theme or "General",
                source=r.source
            )
            quotes.append(quote)
            
    return {"quotes": quotes}
