import os
from langchain_groq import ChatGroq
from core.config import settings

def get_llm(temperature: float = 0.0):
    if not settings.groq_api_key:
        # Fallback to env var if not in settings, or raise an error if needed
        api_key = os.environ.get("GROQ_API_KEY", "")
    else:
        api_key = settings.groq_api_key
        
    return ChatGroq(
        api_key=api_key,
        model_name=settings.groq_model_name,
        temperature=temperature,
        max_tokens=settings.groq_max_tokens,
        max_retries=2
    )

analysis_llm = get_llm(temperature=0.0)
generation_llm = get_llm(temperature=0.3)
