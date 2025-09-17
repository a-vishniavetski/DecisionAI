# ==== main.py ====
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


from _llm import make_response


class DecisionRequest(BaseModel):
    user_question: str

class DecisionResponse(BaseModel):
    response: str

app = FastAPI()

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}

@app.post("/api/chat")
async def chat(request: DecisionRequest):
    user_question = request.user_question

    response = make_response(user_question)

    return DecisionResponse(response=response)

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# Serve React static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")