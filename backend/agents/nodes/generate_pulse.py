import json
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from agents.state import PipelineState
from agents.llm import generation_llm
from agents.prompts.pulse import get_pulse_prompt
from models.outputs import ProductPulse

class PulseOutput(BaseModel):
    top_themes_summary: str = Field(description="Summary of top themes")
    user_voice_summary: str = Field(description="Summary of user voice based on quotes")
    key_observation: str = Field(description="Key observation or takeaway")
    product_actions: list[str] = Field(description="Exactly 3 actionable items")

def generate_pulse(state: PipelineState) -> dict:
    print("--- GENERATE PULSE ---")
    
    themes = state.get("themes", [])
    quotes = state.get("quotes", [])
    fee_issue = state.get("fee_issue")
    
    llm = generation_llm
    llm_with_tool = llm.with_structured_output(PulseOutput, method="json_mode")
    
    prompt = get_pulse_prompt()
    
    context = f"Themes: {[t.model_dump() for t in themes]}\n"
    context += f"Quotes: {[q.model_dump() for q in quotes]}\n"
    if fee_issue:
        context += f"Fee Issue: {fee_issue.model_dump()}\n"
        
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Generate the Pulse based on this data:\n{context}")
    ]
    
    result = llm_with_tool.invoke(messages)
    
    # Construct full content for display
    content = f"**Top Themes Summary:**\n{result.top_themes_summary}\n\n"
    content += f"**User Voice:**\n{result.user_voice_summary}\n\n"
    content += f"**Key Observation:**\n{result.key_observation}\n\n"
    content += "**Product Actions:**\n"
    for i, action in enumerate(result.product_actions):
        content += f"{i+1}. {action}\n"
        
    word_count = len(content.split())
    
    pulse = ProductPulse(
        content=content,
        word_count=word_count,
        top_themes_summary=result.top_themes_summary,
        user_voice_quotes=quotes, # Using actual quotes from state
        key_observation=result.key_observation,
        product_actions=result.product_actions[:3] # Ensure exactly 3
    )
    
    return {
        "product_pulse": pulse,
        "analysis_status": "generate_pulse_completed"
    }
