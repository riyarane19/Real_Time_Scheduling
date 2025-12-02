from pydantic import BaseModel, Field
from typing import List


class Task(BaseModel):
    name: str = Field(..., description="Task name")
    execution_time: float = Field(..., gt=0, description="WCET / execution time in ms")
    period: float = Field(..., gt=0, description="Task period in ms")
    deadline: float = Field(..., gt=0, description="Relative deadline in ms")


class SimulationRequest(BaseModel):
    tasks: List[Task]
    algorithm: str = Field(..., description="RM | DM | EDF | LLF")
    duration: float = Field(..., gt=0, description="Simulation time in ms")


class TimeSlot(BaseModel):
    start: float
    end: float
    task: str | None
    deadline_miss: bool = False


class SimulationMetrics(BaseModel):
    cpu_utilization: float
    total_deadline_misses: int
    per_task_deadline_misses: dict
    hyperperiod_approx: float | None = None


class SimulationResponse(BaseModel):
    timeline: List[TimeSlot]
    metrics: SimulationMetrics
