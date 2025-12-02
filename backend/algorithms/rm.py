def rm_priority(job: dict) -> float:
    """
    Rate Monotonic: shorter period -> higher priority (lower value).
    We simply use the period as the priority key.
    """
    return job["period"]
