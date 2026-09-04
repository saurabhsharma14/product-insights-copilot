from langchain_core.prompts import PromptTemplate

CLASSIFY_REVIEW_PROMPT = """You are an expert product analyst for the Groww Android App.
Your task is to classify a batch of user reviews from the Google Play Store.

For each review, you must provide:
- primary_theme: The main topic of the review (e.g., "Login Issues", "Hidden Charges", "UI/UX", "Customer Support", "App Crash"). Be concise.
- secondary_theme: A secondary topic, if any.
- sentiment: "Positive", "Neutral", or "Negative".
- severity: "High" (critical issue, money loss, data loss, app unusable), "Medium" (annoying but usable), "Low" (feature request, minor bug), or "None" (praise).
- issue_type: "Bug", "Feature Request", "UX", "Pricing/Fees", "Customer Service", or "None".

Reviews to classify:
{reviews_json}

Return a valid JSON object with a single key "classifications" containing an array of objects, where each object corresponds to a review in the batch, containing the following keys:
- "review_id": (string, must match the input review_id)
- "primary_theme": (string)
- "secondary_theme": (string or null)
- "sentiment": (string)
- "severity": (string)
- "issue_type": (string or null)
"""

classify_prompt_template = PromptTemplate(
    input_variables=["reviews_json"],
    template=CLASSIFY_REVIEW_PROMPT
)
