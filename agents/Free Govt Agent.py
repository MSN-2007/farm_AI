import requests
from bs4 import BeautifulSoup
from llm_router import ask_llm

async def govt_agent(query: str):

    search_url = f"https://duckduckgo.com/html/?q={query} site:gov.in agriculture advisory"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    snippets = ""

    for result in soup.find_all("a", class_="result__a", limit=5):
        snippets += result.text + "\n"

    extraction_prompt = f"""
Extract official government agricultural advisory data:

{snippets}

Return JSON:
[
  {{
    "source": "Govt Advisory",
    "recommendation": "",
    "dosage": "",
    "method": "",
    "confidence": 0.9
  }}
]
"""

    structured = ask_llm(extraction_prompt)

    try:
        return eval(structured)
    except:
        return []