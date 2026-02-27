import requests
from bs4 import BeautifulSoup
from llm_router import ask_llm

async def research_agent(query: str, domain: str):

    headers = {"User-Agent": "Mozilla/5.0"}

    domain_queries = {
        "fish_farming": f"{query} aquaculture dissolved oxygen aeration mg/L guidelines",
        "cattle_management": f"{query} veterinary treatment mastitis antibiotic protocol dairy",
        "crop_management": f"{query} crop agronomy fertilizer yield research",
        "storage_management": f"{query} grain storage moisture fungal prevention",
    }

    search_query = domain_queries.get(domain, query)

    search_url = f"https://duckduckgo.com/html/?q={search_query}"

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for result in soup.find_all("a", class_="result__a", limit=3):
        href = result.get("href")
        if href:
            links.append(href)

    collected_text = ""

    for link in links:
        try:
            page = requests.get(link, headers=headers, timeout=5)
            page_soup = BeautifulSoup(page.text, "html.parser")
            paragraphs = page_soup.find_all("p")

            for p in paragraphs[:15]:
                collected_text += p.get_text() + "\n"

        except:
            continue

    if not collected_text.strip():
        return []

    extraction_prompt = f"""
Extract only technical intervention methods relevant to {domain}.

Ignore crop fertilizer content if domain is fish or cattle.
Ignore unrelated agriculture topics.

Return JSON list:
[
  {{
    "source": "ResearchPaper",
    "recommendation": "",
    "confidence": 0.75
  }}
]

Text:
{collected_text}
"""

    structured = ask_llm(extraction_prompt)

    try:
        return eval(structured)
    except:
        return []