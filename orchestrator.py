import asyncio
import json
import re
from agents.domain_router import classify_domain
from agents.research_agent import research_agent
from agents.govt_agent import govt_agent
from agents.practical_agent import practical_agent
from llm_router import ask_llm

SAFE_THRESHOLD = 0.75


# ----------------------------------------
# Evidence Scoring
# ----------------------------------------

def calculate_evidence_score(item):
    base = item.get("confidence", 0)

    if item.get("source") == "Govt Advisory":
        base += 0.3
    elif item.get("source") == "ResearchPaper":
        base += 0.2
    elif item.get("source") == "FarmerForum":
        base += 0.05

    return min(base, 1.0)


# ----------------------------------------
# Domain Relevance Filtering
# ----------------------------------------

def is_relevant(item, domain):
    text = str(item).lower()

    # Block obvious fertilizer garbage in wrong domains
    if domain in ["fish_farming", "cattle_management"] and "fertilizer" in text:
        return False

    return True

# ----------------------------------------
# Main Orchestrator
# ----------------------------------------

async def orchestrate(query: str):

    # 1️⃣ Classify domain
    domain = classify_domain(query)

    if domain == "unknown":
        return {
            "status": "uncertain",
            "message": "Unable to classify agriculture domain."
        }

    # 2️⃣ Call agents
    tasks = [
        research_agent(query),
        govt_agent(query),
        practical_agent(query)
    ]

    results = await asyncio.gather(*tasks)

    combined = [item for sublist in results for item in sublist]

    if not combined:
        return {
            "status": "uncertain",
            "message": "No relevant data found."
        }

    # 3️⃣ Evidence Scoring
    for item in combined:
        item["evidence_score"] = calculate_evidence_score(item)

    # 4️⃣ Filter by Evidence + Domain Relevance
    filtered = [
        item for item in combined
        if item["evidence_score"] >= SAFE_THRESHOLD
        and is_relevant(item, domain)
    ]

    if not filtered:
        return {
            "status": "uncertain",
            "message": "No strong domain-relevant verified evidence found."
        }

    # 5️⃣ Final Advisory LLM
    prompt = f"""
You are a professional agricultural technical advisor.

Provide the TOP 5 most effective DISTINCT methods to solve the problem.

Return ONLY valid JSON in this structure:

{{
  "domain": "{domain}",
  "problem": "{query}",
  "top_solutions_ranked": [
      {{
          "rank": 1,
          "method_name": "",
          "core_mechanism": "",
          "why_effective": ""
      }}
  ],
  "confidence_level": "high/medium/low",
  "poll": {{
      "question": "",
      "options": ["", "", "", "", ""]
  }}
}}

STRICT RULES:
- Provide EXACTLY 5 methods.
- Rank them by real-world effectiveness (1 = highest impact).
- Each method must use a different technical mechanism.
- No duplicate wording.
- No step-by-step instructions.
- No long paragraphs.
- No filler explanation.
- Only practical, technically correct solutions.
- Do NOT include unrelated cross-domain advice.
- No vague verbs like "Improve", "Enhance", "Optimize".
- Use specific technical interventions.
- Methods must be practical and widely used.
- Poll options must match method_name exactly.
- Output ONLY JSON.

Verified Evidence:
{filtered}
"""

    analysis = ask_llm(prompt)

    # 6️⃣ Safe JSON Extraction (Repair LLM formatting issues)
    try:
        json_match = re.search(r'\{.*\}', analysis, re.DOTALL)

        if not json_match:
            raise ValueError("No JSON found")

        structured_output = json.loads(json_match.group())

    except Exception:
        return {
            "status": "error",
            "message": "LLM JSON parsing failed",
            "raw_output": analysis
        }

    return {
        "status": "success",
        "data": structured_output
    }