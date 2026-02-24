from fastapi import FastAPI
from orchestrator import orchestrate
import asyncio

app = FastAPI()

@app.post("/ask")
async def ask_ai(question: str):
    result = await orchestrate(question)
    return result