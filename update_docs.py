import os
import re

files = [
    "problemStatement.md", 
    "architecture.md", 
    "implementation_plan.md", 
    "edge-cases.md", 
    "eval.md"
]

for f in files:
    path = os.path.join(os.getcwd(), f)
    if os.path.exists(path):
        with open(path, "r") as file:
            content = file.read()
        
        content = content.replace("12 weeks", "7 days")
        content = content.replace("12 Weeks", "7 Days")
        content = content.replace("12-week", "7-day")
        content = content.replace("12-Week", "7-Day")
        content = content.replace("REVIEW_LOOKBACK_WEEKS=12", "REVIEW_LOOKBACK_DAYS=7")
        content = content.replace("REVIEW_LOOKBACK_WEEKS = 12", "REVIEW_LOOKBACK_DAYS = 7")
        content = content.replace("REVIEW_LOOKBACK_WEEKS", "REVIEW_LOOKBACK_DAYS")
        content = content.replace("review_lookback_weeks: int = 12", "review_lookback_days: int = 7")
        content = content.replace("review_lookback_weeks", "review_lookback_days")
        
        with open(path, "w") as file:
            file.write(content)
        print(f"Updated {f}")
    else:
        print(f"File not found: {f}")
