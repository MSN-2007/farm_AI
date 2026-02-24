import asyncio

async def govt_agent(query: str):
    await asyncio.sleep(0.5)

    return [
        {
            "source": "Govt Advisory",
            "title": "Government Best Practice",
            "recommendation": "Follow Soil Test Based Fertilization",
            "dosage": "As per soil test report",
            "confidence": 0.9
        }
    ]