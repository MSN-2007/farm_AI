import asyncio

async def practical_agent(query: str):
    await asyncio.sleep(0.5)

    return [
        {
            "source": "FarmerForum",
            "title": "Farmer Experience",
            "recommendation": "Improved Field Monitoring",
            "dosage": "Regular observation",
            "confidence": 0.75
        }
    ]