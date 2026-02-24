from llm_router import ask_llm

def classify_domain(query: str):

    prompt = f"""
Classify the agriculture question into ONE domain:

Domains:
- crop_management
- cattle_management
- fish_farming
- storage_management
- soil_management
- irrigation
- unknown

Question:
{query}

Return only the domain name.
"""

    result = ask_llm(prompt).strip().lower()

    return result