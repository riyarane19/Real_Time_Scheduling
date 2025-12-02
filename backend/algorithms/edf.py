def edf_priority(job: dict, now: int) -> float:
    """
    Earliest Deadline First: earliest absolute deadline wins.
    """
    return job["abs_deadline"]
