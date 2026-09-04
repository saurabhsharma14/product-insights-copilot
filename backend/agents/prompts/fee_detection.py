from langchain_core.prompts import PromptTemplate

FEE_DETECTION_PROMPT = """You are an expert product analyst for the Groww Android App.
Your task is to scan the provided classified user reviews and detect if there is a recurring fee or charge confusion among users.

Reviews:
{reviews_json}

Look for patterns like "Why was I charged?", "What is this fee?", "hidden charges", or similar complaints.
If there are multiple issues, select the strongest recurring issue.
You MUST NOT pre-assume a specific fee—it must emerge from the data.

If a fee confusion issue is found, provide:
- fee_name: A short name for the fee (e.g., "AMC Charge", "DP Charges").
- observed_misunderstanding: A brief explanation of what users are confused about.
- confidence: "High", "Medium", or "Low".
- selection_reason: Why this issue was selected over others (or just why it's notable).
- representative_complaints: A list of exactly 3 review_ids that illustrate this confusion.

If NO fee confusion is found in the data, return a JSON object with "has_fee_issue" set to false.

Return a valid JSON object matching this schema:
{{
  "has_fee_issue": true/false,
  "fee_name": string or null,
  "observed_misunderstanding": string or null,
  "confidence": string or null,
  "selection_reason": string or null,
  "representative_complaints": array of strings or null
}}
"""

fee_detection_prompt_template = PromptTemplate(
    input_variables=["reviews_json"],
    template=FEE_DETECTION_PROMPT
)
