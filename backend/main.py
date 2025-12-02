from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import SimulationRequest, SimulationResponse
from scheduler import simulate


app = FastAPI(
    title="Real-Time Scheduling Dashboard API",
    description="Simple scheduler simulator (RM/DM/EDF/LLF) without SimSo.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/simulate", response_model=SimulationResponse)
def run_simulation(request: SimulationRequest):
    if request.algorithm not in {"RM", "DM", "EDF", "LLF"}:
        raise HTTPException(status_code=400, detail="Unsupported algorithm")

    if not request.tasks:
        raise HTTPException(status_code=400, detail="At least one task is required")

    response = simulate(request)
    return response
