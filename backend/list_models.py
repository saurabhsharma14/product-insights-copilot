import os
# pyrefly: ignore [missing-import]
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.groq_api_key)
models = client.models.list()
for m in models.data:
    print(m.id)
