from .base_data import JobParsedBaseData
from dataclasses import dataclass
from typing import Any

@dataclass
class Job:
    """
    Class for all data associated with a job, including calculated data.
    """

    # The JNID that uniquely identifies the job.
    jnid: str

    # The raw JSON data from the JobNimbus API for base data that appears in
    # https://app.jobnimbus.com/api1/jobs/<jnid>
    raw_base_data: dict[str, Any]
    # The raw JSON data from the JobNimbus API for activities that appear in
    # https://app.jobnimbus.com/api1/activities associated with this job
    raw_activities: dict[str, Any]

    parsed: JobParsedBaseData

