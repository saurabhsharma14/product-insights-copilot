from langchain_core.prompts import PromptTemplate

CLUSTER_THEMES_PROMPT = """You are an expert product analyst for the Groww Android App.
Your task is to identify up to 5 emergent themes from the classified user reviews provided.

Reviews:
{reviews_json}

Identify up to 5 main themes that encompass these reviews. For each theme, provide:
- theme_name: A concise, descriptive name (e.g., "Account Verification Delays", "Hidden Charges").
- description: A brief summary of what users are experiencing.
- representative_review_ids: A list of exactly 3 review_ids that best represent this theme.

Return a valid JSON object with a single key "themes" containing an array of objects, where each object corresponds to a theme, containing the following keys:
- "theme_name": (string)
- "description": (string)
- "representative_review_ids": (array of strings)
"""

cluster_prompt_template = PromptTemplate(
    input_variables=["reviews_json"],
    template=CLUSTER_THEMES_PROMPT
)
