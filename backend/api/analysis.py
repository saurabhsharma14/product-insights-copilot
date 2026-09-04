import json
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from agents.graph import build_graph
from core.database import get_db
from models.review import ReviewRecord
from models.theme import Theme
from models.fee_issue import FeeIssue

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

stream_queues = {}
stream_event_cache = {}
graph = build_graph()

def _push_event(batch_id: str, step: str, status: str, message: str):
    event = {"step": step, "status": status, "message": message}
    
    if batch_id not in stream_event_cache:
        stream_event_cache[batch_id] = []
    stream_event_cache[batch_id].append(event)
    
    if batch_id in stream_queues:
        for q in stream_queues[batch_id]:
            asyncio.create_task(q.put(event))

async def run_analysis_pipeline(batch_id: str):
    try:
        async with get_db() as db:
            rows = await db.fetch("SELECT * FROM reviews WHERE batch_id = $1", batch_id)
                
        if not rows:
            _push_event(batch_id, "Error", "error", "No reviews found for this batch")
            return
            
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
            
        state = {
            "batch_id": batch_id,
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
        
        _push_event(batch_id, "Reviews loaded", "done", f"Loaded {len(reviews)} reviews")
        
        current_state = state
        async for output in graph.astream(state):
            for node_name, node_state in output.items():
                current_state = {**current_state, **node_state}
                if node_name == "classify_reviews":
                    _push_event(batch_id, "Reviews cleaned", "done", "Classified and cleaned reviews")
                elif node_name == "cluster_themes":
                    _push_event(batch_id, "Themes identified", "done", "Clustered reviews into themes")
                elif node_name == "rank_themes":
                    _push_event(batch_id, "Themes ranked", "done", "Ranked top themes")
                elif node_name == "detect_fee":
                    _push_event(batch_id, "Fee confusion detected", "done", "Scanned for fee confusions")
                elif node_name == "extract_quotes":
                    _push_event(batch_id, "Quotes extracted", "done", "Extracted representative quotes")
                elif node_name == "analyze_trends":
                    _push_event(batch_id, "Trends analyzed", "done", "Analyzed temporal trends")
                elif node_name == "verify_sources":
                    _push_event(batch_id, "Official sources verified", "done", "Verified official sources")
                elif node_name == "generate_pulse":
                    _push_event(batch_id, "Product Pulse generated", "done", "Generated Product Pulse")
                elif node_name == "generate_explainer":
                    _push_event(batch_id, "Fee Explainer generated", "done", "Generated Fee Explainer")
                    
        # Persist to DB
        async with get_db() as db:
            themes_json = json.dumps([t.model_dump() for t in current_state.get("themes", [])]) if current_state.get("themes") else "[]"
            fee_issue_json = json.dumps(current_state["fee_issue"].model_dump()) if current_state.get("fee_issue") else None
            quotes_json = json.dumps([q.model_dump() for q in current_state.get("quotes", [])]) if current_state.get("quotes") else "[]"
            pulse_json = json.dumps(current_state["product_pulse"].model_dump()) if current_state.get("product_pulse") else None
            explainer_json = json.dumps(current_state["fee_explainer"].model_dump()) if current_state.get("fee_explainer") else None
            
            await db.execute("""
                UPDATE analysis_runs 
                SET themes = $1, fee_issues = $2, status = 'completed'
                WHERE batch_id = $3
            """, themes_json, fee_issue_json, batch_id)
            
            await db.execute("""
                UPDATE analysis_runs 
                SET product_pulse = $1, fee_explainer = $2
                WHERE batch_id = $3
            """, pulse_json, explainer_json, batch_id)

        _push_event(batch_id, "Analysis complete", "done", "Pipeline finished")
    except Exception as e:
        import traceback
        traceback.print_exc()
        _push_event(batch_id, "Pipeline error", "error", str(e))

@router.post("/run/{batch_id}")
async def run_analysis(batch_id: str, background_tasks: BackgroundTasks):
    if batch_id not in stream_queues:
        stream_queues[batch_id] = []
        stream_event_cache[batch_id] = []
    background_tasks.add_task(run_analysis_pipeline, batch_id)
    return {"status": "started", "batch_id": batch_id}

@router.get("/stream/{batch_id}")
async def stream_analysis(batch_id: str):
    if batch_id not in stream_queues:
        stream_queues[batch_id] = []
        
    q = asyncio.Queue()
    
    if batch_id in stream_event_cache:
        for event in stream_event_cache[batch_id]:
            q.put_nowait(event)
            
    stream_queues[batch_id].append(q)
    
    async def event_generator():
        try:
            while True:
                event = await q.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event["status"] == "error" or event["step"] == "Analysis complete":
                    break
        finally:
            if q in stream_queues[batch_id]:
                stream_queues[batch_id].remove(q)
                
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/results/{batch_id}")
async def get_results(batch_id: str):
    async with get_db() as db:
        row = await db.fetchrow("SELECT themes, fee_issues, product_pulse, fee_explainer, review_count FROM analysis_runs WHERE batch_id = $1", batch_id)
        if not row:
            raise HTTPException(status_code=404, detail="Batch not found")
            
        product_pulse = json.loads(row[2]) if row[2] else None
        quotes = product_pulse.get("user_voice_quotes", []) if product_pulse else []
        
        return {
            "themes": json.loads(row[0]) if row[0] else [],
            "fee_issue": json.loads(row[1]) if row[1] else None,
            "product_pulse": product_pulse,
            "fee_explainer": json.loads(row[3]) if row[3] else None,
            "quotes": quotes,
            "review_count": row[4] or 0
        }

@router.get("/runs")
async def get_analysis_runs():
    """Returns all historical analysis runs for the dashboard."""
    async with get_db() as db:
        rows = await db.fetch('''
            SELECT batch_id, status, review_count, review_period_start, review_period_end, 
                   avg_rating, created_at, approved_at, mcp_document_status, mcp_gmail_status
            FROM analysis_runs 
            ORDER BY created_at DESC
        ''')
            
        return [{"batch_id": r[0], "status": r[1], "review_count": r[2], 
                 "review_period_start": r[3], "review_period_end": r[4], 
                 "avg_rating": r[5], "created_at": r[6], "approved_at": r[7],
                 "document_action_status": r[8], "gmail_action_status": r[9]} for r in rows]
