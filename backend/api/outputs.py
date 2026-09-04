from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.database import get_db
import json

router = APIRouter(prefix="/api/outputs", tags=["outputs"])

class PulseUpdateReq(BaseModel):
    content: str

class ExplainerUpdateReq(BaseModel):
    customer_confusion_summary: str
    bullets: list[str]

@router.put("/{batch_id}/pulse")
async def update_pulse(batch_id: str, req: PulseUpdateReq):
    async with get_db() as db:
        row = await db.fetchrow("SELECT product_pulse FROM analysis_runs WHERE batch_id = $1", batch_id)
        if not row:
            raise HTTPException(status_code=404, detail="Batch not found")
            
        pulse_data = json.loads(row[0]) if row[0] else {}
        pulse_data["content"] = req.content
        pulse_data["word_count"] = len(req.content.split())
        
        await db.execute(
            "UPDATE analysis_runs SET product_pulse = $1 WHERE batch_id = $2",
            json.dumps(pulse_data), batch_id
        )
        return {"status": "success"}

@router.put("/{batch_id}/explainer")
async def update_explainer(batch_id: str, req: ExplainerUpdateReq):
    async with get_db() as db:
        row = await db.fetchrow("SELECT fee_explainer FROM analysis_runs WHERE batch_id = $1", batch_id)
        if not row:
            raise HTTPException(status_code=404, detail="Batch not found")
            
        explainer_data = json.loads(row[0]) if row[0] else {}
        explainer_data["customer_confusion_summary"] = req.customer_confusion_summary
        explainer_data["bullets"] = req.bullets
        
        await db.execute(
            "UPDATE analysis_runs SET fee_explainer = $1 WHERE batch_id = $2",
            json.dumps(explainer_data), batch_id
        )
        return {"status": "success"}
