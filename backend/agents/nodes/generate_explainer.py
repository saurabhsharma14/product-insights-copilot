from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from agents.state import PipelineState
from agents.llm import get_llm
from agents.prompts.explainer import get_explainer_prompt
from models.outputs import FeeExplainer

class ExplainerOutput(BaseModel):
    customer_confusion_summary: str = Field(description="Summary of the customer confusion")
    bullets: list[str] = Field(description="Maximum 6 bullets explaining the fee based on sources")

def generate_explainer(state: PipelineState) -> dict:
    print("--- GENERATE EXPLAINER ---")
    
    fee_issue = state.get("fee_issue")
    official_sources = state.get("official_sources", [])
    
    if not fee_issue or not official_sources:
        return {"fee_explainer": None}
        
    llm = get_llm()
    llm_with_tool = llm.with_structured_output(ExplainerOutput, method="json_mode")
    
    prompt_template = PromptTemplate(
        input_variables=["fee_name", "misunderstanding", "sources"],
        template=get_explainer_prompt()
    )
    
    context = f"Fee Issue: {fee_issue.model_dump()}\n"
    context += f"Official Sources: {[s.model_dump() for s in official_sources]}\n"
    
    messages = [
        SystemMessage(content=prompt_template.format(fee_name=fee_issue.fee_name, misunderstanding=fee_issue.observed_misunderstanding, sources=context)),
        HumanMessage(content=f"Generate the Explainer based on this data:\n{context}")
    ]
    
    try:
        result = llm_with_tool.invoke(messages)
        
        explainer = FeeExplainer(
            fee_name=fee_issue.fee_name,
            customer_confusion_summary=result.customer_confusion_summary,
            bullets=result.bullets[:6], # Ensure max 6
            sources=official_sources,
            last_checked=datetime.utcnow().isoformat() + "Z"
        )
        
        return {
            "fee_explainer": explainer,
            "analysis_status": "generate_explainer_completed"
        }
    except Exception as e:
        print(f"--- GENERATE EXPLAINER FAILED: {e} ---")
        return {
            "fee_explainer": None,
            "analysis_status": "generate_explainer_failed"
        }
