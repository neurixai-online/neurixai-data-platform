from fastapi import FastAPI

from app.domains.environment_data.router import router as environment_data_router
from app.domains.platform.router import router as platform_router
from app.domains.reference_data.router import router as reference_data_router

app = FastAPI(title="NeurixAI Data Platform — Core API")

app.include_router(reference_data_router)
app.include_router(environment_data_router)
app.include_router(platform_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
