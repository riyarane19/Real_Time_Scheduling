from typing import List, Dict, Callable
from math import gcd
from functools import reduce

from models import SimulationRequest, SimulationResponse, TimeSlot, SimulationMetrics
from algorithms.rm import rm_priority
from algorithms.dm import dm_priority
from algorithms.edf import edf_priority
from algorithms.llf import llf_priority


def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def lcm_list(values: List[int]) -> int:
    return reduce(lcm, values)


def simulate(request: SimulationRequest) -> SimulationResponse:
    """
    Very simple discrete-time scheduler simulation:
    - Time step = 1 ms
    - Periodic tasks: instances released every 'period'
    - Each instance has its own absolute deadline
    - Preemptive: at each time step, choose highest-priority ready job
    """
    tasks = request.tasks
    algorithm = request.algorithm
    duration = int(request.duration)

    # Build runtime structures
    jobs: List[Dict] = []
    deadline_misses: Dict[str, int] = {t.name: 0 for t in tasks}
    timeline: List[TimeSlot] = []

    # Map algorithm -> priority function
    def make_priority_func(algo: str) -> Callable[[Dict, int], float]:
        if algo == "RM":
            return lambda job, now: rm_priority(job)
        if algo == "DM":
            return lambda job, now: dm_priority(job)
        if algo == "EDF":
            return lambda job, now: edf_priority(job, now)
        if algo == "LLF":
            return lambda job, now: llf_priority(job, now)
        raise ValueError("Unknown algorithm")

    priority_fn = make_priority_func(algorithm)

    # Approx hyperperiod
    try:
        hyper = lcm_list([int(t.period) for t in tasks])
    except Exception:
        hyper = None

    last_task_name = None
    current_slot_start = 0

    for time in range(duration):
        # Release new jobs
        for t in tasks:
            if time % int(t.period) == 0:
                jobs.append(
                    {
                        "task_name": t.name,
                        "remaining": t.execution_time,
                        "period": t.period,
                        "relative_deadline": t.deadline,
                        "release_time": time,
                        "abs_deadline": time + t.deadline,
                    }
                )

        # Check for deadline misses (jobs that are not finished but deadline passed)
        for job in jobs:
            if not job.get("completed") and time > job["abs_deadline"]:
                job["deadline_missed"] = True
                deadline_misses[job["task_name"]] += 1
                job["completed"] = True

        # Select ready and not completed jobs
        ready_jobs = [
            job for job in jobs if not job.get("completed") and job["release_time"] <= time
        ]

        running_task_name = None
        deadline_miss_flag = False

        if ready_jobs:
            # Choose job with minimum priority value
            job = min(ready_jobs, key=lambda j: priority_fn(j, time))
            running_task_name = job["task_name"]
            # Execute for 1 ms
            job["remaining"] -= 1
            if job["remaining"] <= 0:
                job["completed"] = True
                if time + 1 > job["abs_deadline"]:
                    # If it completed after deadline
                    deadline_misses[job["task_name"]] += 1
                    deadline_miss_flag = True

        # Record timeslot (merge consecutive same-task slots later)
        if last_task_name is None:
            # first slot
            current_slot_start = time
            last_task_name = running_task_name
        else:
            if running_task_name != last_task_name:
                # close previous slot
                timeline.append(
                    TimeSlot(
                        start=current_slot_start,
                        end=time,
                        task=last_task_name,
                        deadline_miss=False,
                    )
                )
                current_slot_start = time
                last_task_name = running_task_name

    # Close last slot
    timeline.append(
        TimeSlot(
            start=current_slot_start,
            end=duration,
            task=last_task_name,
            deadline_miss=False,
        )
    )

    # Compute utilization
    total_exec = sum(t.execution_time / t.period for t in tasks)
    utilization = float(total_exec * 100.0)

    metrics = SimulationMetrics(
        cpu_utilization=utilization,
        total_deadline_misses=sum(deadline_misses.values()),
        per_task_deadline_misses=deadline_misses,
        hyperperiod_approx=hyper,
    )

    return SimulationResponse(timeline=timeline, metrics=metrics)
