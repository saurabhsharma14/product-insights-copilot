from agents.state import PipelineState
from services.source_retriever import OfficialSourceRetriever

async def verify_sources(state: PipelineState) -> dict:
    print("--- VERIFY SOURCES ---")
    fee_issue = state.get("fee_issue")
    
    if not fee_issue:
        return {"official_sources": [], "analysis_status": "verify_sources_skipped"}
        
    retriever = OfficialSourceRetriever()
    sources = await retriever.search_fee_documentation(fee_issue.fee_name)
    
    return {
        "official_sources": sources,
        "analysis_status": "verify_sources_completed"
    }
