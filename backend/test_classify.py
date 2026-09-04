import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db
from models.review import ReviewRecord
from agents.nodes.classify_reviews import classify_reviews_node

async def test():
    print("Fetching 5 reviews from DB...")
    async with get_db() as db:
        async with db.execute("SELECT * FROM reviews LIMIT 5") as cursor:
            rows = await cursor.fetchall()
            
    reviews = []
    for r in rows:
        reviews.append(ReviewRecord(
            review_id=r["review_id"],
            review_text=r["review_text"],
            rating=r["rating"],
            review_date=r["review_date"],
            app_version=r["app_version"],
            developer_reply=r["developer_reply"],
            source=r["source"],
            source_url=r["source_url"]
        ))
        
    print(f"Loaded {len(reviews)} reviews. Running pipeline...")
    state = {
        "batch_id": "test_batch",
        "reviews": reviews,
        "classified_reviews": [],
        "themes": [],
        "fee_issue": None,
        "official_sources": [],
        "product_pulse": None,
        "fee_explainer": None,
        "quotes": [],
        "analysis_status": "running"
    }
    
    from agents.graph import build_graph
    graph = build_graph()
    
    try:
        async for output in graph.astream(state):
            for node_name, node_state in output.items():
                print(f"Completed node: {node_name}")
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
