def dm_priority(job: dict) -> float:
    """
    Deadline Monotonic: shorter relative deadline -> higher priority.
    We use the relative deadline field from the job.
    """
    return job["relative_deadline"]
