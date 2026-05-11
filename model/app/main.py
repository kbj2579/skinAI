from fastapi import FastAPI
from app.routers import skin, scalp, lesion

app = FastAPI(title="Skin AI Model Server (Mock)", version="0.1.0")

app.include_router(skin.router)
app.include_router(scalp.router)
app.include_router(lesion.router)


@app.get("/health")
async def health():
    return {"status": "ok", "mode": "mock"}
