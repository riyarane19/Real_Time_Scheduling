from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple
from math import gcd
from functools import reduce
from fastapi import FastAPI, Response
from utils.pdf_utils import generate_schedule_pdf

# -----------------------------
# FastAPI app + CORS
# -----------------------------
app = FastAPI()

# NOTE:
# FastAPI/Starlette CORS: you should NOT use allow_credentials=True with allow_origins=["*"].
# For a local frontend (python http.server on :3000), explicitly allow those origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"ok": True}


# -----------------------------
# Request/response models
# -----------------------------
class Task(BaseModel):
    name: str
    period: int
    execution_time: int
    deadline: Optional[int] = None


class ScheduleRequest(BaseModel):
    tasks: List[Task]
    algorithm: str
    simulation_time: int


# -----------------------------
# Helpers (Pydantic v1/v2 safe)
# -----------------------------
def copy_task(t: Task) -> Task:
    if hasattr(t, "model_copy"):  # pydantic v2
        return t.model_copy()
    return Task(**t.dict())  # pydantic v1


def dump_task(t: Task) -> Dict:
    if hasattr(t, "model_dump"):  # pydantic v2
        return t.model_dump()
    return t.dict()  # pydantic v1


def lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


def hyperperiod(periods: List[int]) -> int:
    if not periods:
        return 0
    return reduce(lcm, periods)


# -----------------------------
# Scheduling core
# -----------------------------
class Job:
    """
    One released instance ("job") of a periodic task.
    key = (task_name, release_time) uniquely identifies a job.
    """
    __slots__ = ("key", "task_name", "release", "abs_deadline", "remaining", "rel_deadline", "period")

    def __init__(
        self,
        task_name: str,
        release: int,
        abs_deadline: int,
        remaining: int,
        rel_deadline: int,
        period: int,
    ):
        self.key = (task_name, release)
        self.task_name = task_name
        self.release = release
        self.abs_deadline = abs_deadline
        self.remaining = remaining
        self.rel_deadline = rel_deadline
        self.period = period


def job_priority(job: Job, algo: str, now: int) -> Tuple:
    """
    Smaller tuple => higher priority.

    RM  : smallest period first (fixed priority)
    DM  : smallest relative deadline first (fixed priority)
    EDF : smallest absolute deadline first (dynamic priority)
    LLF : smallest laxity first (dynamic priority)
          laxity = (abs_deadline - now) - remaining
    """
    if algo == "RM":
        return (job.period, job.task_name, job.release)

    if algo == "DM":
        return (job.rel_deadline, job.task_name, job.release)

    if algo == "EDF":
        return (job.abs_deadline, job.task_name, job.release)

    # LLF
    laxity = (job.abs_deadline - now) - job.remaining
    return (laxity, job.abs_deadline, job.task_name, job.release)


def simulate(tasks: List[Task], algo: str, sim_time: int) -> Tuple[List[Dict], Dict[str, int], int]:

    """
    Discrete-time, preemptive, single-core simulation with 1 ms quanta.

    Deadline miss convention (important):
    - At time boundary t, BEFORE executing the CPU for interval [t, t+1),
      any job with abs_deadline == t must already be finished.
      If remaining > 0 at that boundary => 1 deadline miss for that job.
    - We also check at t == sim_time (end of horizon) so deadlines exactly at sim_time are counted.
    """
    misses: Dict[str, int] = {t.name: 0 for t in tasks}
    timeline_raw: List[Optional[str]] = [None] * sim_time
    preemptive_switches = 0

    # Track the job that was running in the previous tick (for LLF anti-thrashing)
    current_job_key = None  # will store (task_name, release)

    # Precompute releases
    releases_by_time: Dict[int, List[str]] = {}
    task_map: Dict[str, Task] = {t.name: t for t in tasks}

    for t in tasks:
        r = 0
        while r < sim_time:
            releases_by_time.setdefault(r, []).append(t.name)
            r += t.period

    # Active jobs and deadline index
    active: Dict[Tuple[str, int], Job] = {}                 # (task_name, release) -> Job
    deadlines_at: Dict[int, List[Tuple[str, int]]] = {}     # abs_deadline -> [job_key...]

    def mark_deadline_misses(at_time: int) -> None:
        """Count misses for jobs whose deadline is exactly at_time and are not finished."""
        nonlocal current_job_key
        for key in deadlines_at.get(at_time, []):
            j = active.get(key)
            if j is not None and j.remaining > 0:
                misses[j.task_name] += 1
                # Drop job so it won't be counted again
                del active[key]
                # If we dropped the currently running job, clear it
                if current_job_key == key:
                    current_job_key = None

    for now in range(sim_time):
        # 1) Deadline checks at boundary "now"
        mark_deadline_misses(now)

        # 2) Release new jobs at "now"
        for task_name in releases_by_time.get(now, []):
            t = task_map[task_name]
            rel_deadline = int(t.deadline if t.deadline is not None else t.period)
            abs_dl = now + rel_deadline

            j = Job(
                task_name=task_name,
                release=now,
                abs_deadline=abs_dl,
                remaining=int(t.execution_time),
                rel_deadline=rel_deadline,
                period=int(t.period),
            )
            active[j.key] = j
            deadlines_at.setdefault(abs_dl, []).append(j.key)

        # 3) Select job to run for this 1 ms slot
        ready = list(active.values())
        if not ready:
            timeline_raw[now] = None
            current_job_key = None
            continue

        # Candidate chosen by the algorithm
        ready.sort(key=lambda x: job_priority(x, algo, now))
        candidate = ready[0]

        current = candidate
        # ------------------------------------------
                    # ✅ PREEMPTIVE SWITCH COUNT
        # A preemption occurs if a different job is scheduled while the previous one is still active.
        if current_job_key is not None and current_job_key in active:
            if current.key != current_job_key:
                preemptive_switches += 1

        current.remaining -= 1
        timeline_raw[now] = current.task_name
        current_job_key = current.key

        if current.remaining <= 0:
            # finished: remove so it won't miss later
            del active[current.key]
            current_job_key = None

    # Final boundary check at end of horizon
    mark_deadline_misses(sim_time)

    # Compress timeline into segments
    segments: List[Dict] = []
    if sim_time == 0:
        return segments, misses,0 

    cur_task = timeline_raw[0]
    cur_start = 0
    for i in range(1, sim_time + 1):
        tname = timeline_raw[i] if i < sim_time else None
        if tname != cur_task:
            segments.append({"start": cur_start, "end": i, "task": cur_task})
            cur_task = tname
            cur_start = i

    segments = [s for s in segments if s["start"] < s["end"]]
    return segments, misses, preemptive_switches

# -----------------------------
# API endpoint
# -----------------------------
@app.post("/schedule")
def schedule(req: ScheduleRequest):
    tasks = [copy_task(t) for t in req.tasks]
    algo = (req.algorithm or "").strip().upper()
    sim_time = int(req.simulation_time)

    # Debug (optional)
    print("ALGO RECEIVED RAW =", req.algorithm)
    print("TASKS RECEIVED =", [(t.name, t.period, t.execution_time, t.deadline) for t in req.tasks])

    if sim_time <= 0:
        return {"error": "simulation_time must be > 0"}
    if not tasks:
        return {"error": "tasks must not be empty"}

    # Normalize + validate
    for t in tasks:
        if t.period <= 0 or t.execution_time <= 0:
            return {"error": "period and execution_time must be > 0"}
        if t.deadline is None:
            t.deadline = t.period
        if t.deadline <= 0:
            return {"error": "deadline must be > 0"}
        if t.execution_time > 10_000 or t.period > 1_000_000:
            return {"error": "unreasonable values detected (check inputs)"}

    supported = {"RM", "DM", "EDF", "LLF"}
    if algo not in supported:
        return {"error": f"Unsupported algorithm '{req.algorithm}'. Use one of: RM, DM, EDF, LLF."}

    timeline, misses_by_task, preemptive_switches = simulate(tasks, algo, sim_time)


    util = sum(t.execution_time / t.period for t in tasks)
    total_misses = sum(misses_by_task.values())
    hp = hyperperiod([t.period for t in tasks])

    return {
        "algorithm": algo,
        "simulation_time": sim_time,
        "tasks": [dump_task(t) for t in tasks],
        "timeline": timeline,
        "metrics": {
            "cpu_utilization": util,
            "preemptive_switches": preemptive_switches,
            "total_deadline_misses": total_misses,
            "deadline_misses_by_task": misses_by_task,
            "hyperperiod": hp,
        },
    }
@app.post("/export/pdf")
def export_pdf(data: dict):
    pdf = generate_schedule_pdf(
        input_data=data["input"],
        output_data=data["output"]
    )

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=schedule_report.pdf"
        }
    )
