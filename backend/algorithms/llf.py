def llf_priority(job: dict, now: int) -> float:
    """
    Least Laxity First: laxity = (abs_deadline - now - remaining).
    Lower laxity => higher priority.
    """
    laxity = job["abs_deadline"] - now - job["remaining"]
    return laxity
