import html
import re
from typing import List, Dict, Tuple
from models.review import ReviewRecord

class ReviewCleaner:
    def clean(self, reviews: List[ReviewRecord]) -> Tuple[List[ReviewRecord], Dict[str, int]]:
        stats = {
            "total_initial": len(reviews),
            "removed_empty": 0,
            "removed_duplicates": 0,
            "total_valid": 0
        }
        
        seen_texts = set()
        cleaned_reviews = []
        
        for r in reviews:
            text = r.review_text
            
            if not text or not text.strip():
                stats["removed_empty"] += 1
                continue
                
            text = html.unescape(text)
            text = re.sub(r'<[^>]+>', '', text)
            text = text.replace('\u200b', '')
            
            text = re.sub(r'\s+', ' ', text).strip()
            
            if not text:
                 stats["removed_empty"] += 1
                 continue
                 
            text_lower = text.lower()
            if text_lower in seen_texts:
                stats["removed_duplicates"] += 1
                continue
                
            seen_texts.add(text_lower)
            
            r.review_text = text
            cleaned_reviews.append(r)
            
        stats["total_valid"] = len(cleaned_reviews)
        return cleaned_reviews, stats
