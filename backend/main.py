# ==== main.py ====
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI!"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# Serve React static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")