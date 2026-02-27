import asyncio
import json
import re
from agents.domain_router import classify_domain
from agents.research_agent import research_agent
from agents.govt_agent import govt_agent
from agents.practical_agent import practical_agent
from llm_router import ask_llm

SAFE_THRESHOLD = 0.65


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


def calculate_impact_score(item):
    impact = item.get("evidence_score", 0)

    if item.get("source") == "Govt Advisory":
        impact += 0.2
    if item.get("source") == "ResearchPaper":
        impact += 0.1

    return impact


# ----------------------------------------
# Domain Relevance Filtering
# ----------------------------------------

def is_relevant(item, domain):
    text = str(item).lower()

    # Example basic protection against cross-domain contamination
    if domain in ["fish_farming", "cattle_management"] and "fertilizer" in text:
        return False

    return True


# ----------------------------------------
# Semantic Duplicate Removal (Domain-Universal)
# ----------------------------------------

def remove_semantic_duplicates(solutions):
    unique = []
    mechanisms_seen = []

    for sol in solutions:
        mechanism = sol.get("core_mechanism", "").lower()
        duplicate = False

        for existing in mechanisms_seen:
            overlap = len(set(mechanism.split()) & set(existing.split()))
            if overlap > 3:
                duplicate = True
                break

        if not duplicate:
            mechanisms_seen.append(mechanism)
            unique.append(sol)

    return unique


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

    # 2️⃣ Call domain-aware agents
    tasks = [
        research_agent(query, domain),
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

    # 3️⃣ Evidence scoring
    for item in combined:
        item["evidence_score"] = calculate_evidence_score(item)

    # 4️⃣ Filter by evidence threshold + domain relevance
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

    # 5️⃣ Impact ranking
    for item in filtered:
        item["impact_score"] = calculate_impact_score(item)

    filtered = sorted(filtered, key=lambda x: x["impact_score"], reverse=True)

    # Reduce noise
    filtered = filtered[:10]

    # 6️⃣ Final Advisory LLM Prompt (Domain-Universal)
    prompt = f"""
You are a professional agricultural technical advisor.

Provide the TOP 5 most effective DISTINCT corrective methods 
to solve the stated agricultural problem.

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
- Provide EXACTLY 5 direct corrective methods.
- Each method must directly solve the stated problem.
- Exclude monitoring, diagnosis, advisory-only steps.
- No duplicate mechanisms.
- Each method must represent a different intervention approach.
- Keep responses short and technical.
- No vague verbs.
- Poll options must match method_name exactly.
- Output ONLY JSON.

Verified Evidence:
{filtered}
"""

    analysis = ask_llm(prompt)

    # 7️⃣ Safe JSON Extraction
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

    # 8️⃣ Enforce semantic uniqueness
    solutions = structured_output.get("top_solutions_ranked", [])
    solutions = remove_semantic_duplicates(solutions)

    if len(solutions) < 5:
        return {
            "status": "uncertain",
            "message": "Generated solutions overlap or are not sufficiently distinct."
        }

    structured_output["top_solutions_ranked"] = solutions[:5]

    return {
        "status": "success",
        "data": structured_output
    }