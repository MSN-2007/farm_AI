from fastapi import FastAPI
from orchestrator import orchestrate

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Agri AI Running"}

@app.post("/ask")
async def ask_ai(question: str):
    result = await orchestrate(question)
    return result