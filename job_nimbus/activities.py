import re
from .base_data import JobStatus
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class JnActivity:
    primary_jnid: str
    timestamp: datetime
    record_type_name: str
    text: str

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> 'JnActivity':
        return JnActivity(
            primary_jnid=json['primary']['id'],
            timestamp=datetime.fromtimestamp(json['date_created']),
            record_type_name=json['record_type_name'],
            text=json['note']
        )

@dataclass
class JnActivityJobCreated(JnActivity):
    @classmethod
    def from_json(cls, json: dict[str, Any]) -> 'JnActivityJobCreated':
        return JnActivityJobCreated(
            **super().from_json(json).__dict__
        )

@dataclass
class JnActivityStatusChanged(JnActivity):
    old_status: JobStatus
    new_status: JobStatus

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> 'JnActivityStatusChanged':
        # the field in the activity object that contains information about the associated job
        job_info = json['primary']
        try:
            import app_data.global_data as gd
            old_status = gd.jn_job_statuses.value[job_info['old_status']]
            new_status = gd.jn_job_statuses.value[job_info['new_status']]
            return JnActivityStatusChanged(
                **super().from_json(json).__dict__,
                old_status=old_status,
                new_status=new_status
            )
        except KeyError as e:
            raise ValueError("The old and new statuses were not found.", e)

@dataclass
class JnActivityJobModified(JnActivity):
    updates: dict[str, tuple[Any, Any]]

    @classmethod
    def from_json(cls, json: dict[str, Any]) -> 'JnActivityJobModified':
        base = super().from_json(json)

        # parse updates from the text field using regex
        updates = {}
        if base.text and base.text.startswith("Job Updated"):
            # regex pattern to match "FIELDNAME: OLDVALUE => NEWVALUE"
            pattern = r'^([^:\n]+): ([^\n]*) => ([^\n]*)$'
            matches = re.findall(pattern, base.text, re.MULTILINE)
            for match in matches:
                field_name = match[0]
                old_value = match[1]
                new_value = match[2]
                updates[field_name] = (old_value, new_value)
        return JnActivityJobModified(
            **base.__dict__,
            updates=updates
        )

def parse_jn_activity(json: dict[str, Any]) -> JnActivity:
    assert json['primary']['type'] == 'job'

    try:
        match json['record_type_name']:
            case 'Job Created':
                return JnActivityJobCreated.from_json(json)
            case 'Status Changed':
                return JnActivityStatusChanged.from_json(json)
            case 'Job Modified':
                return JnActivityJobModified.from_json(json)
            case _:
                return JnActivity.from_json(json)
    except Exception as e:
        logger.warning(f"Unable to parse JobNimbus activity, falling back to generic JobNimbus activity item: {e}")
        return JnActivity.from_json(json)

def construct_job_status_history(activities: list[JnActivity]) -> list[(datetime, JobStatus)]:
    history = []
    for activity in sorted(activities, key=lambda x: x.timestamp):
        if isinstance(activity, JnActivityJobCreated):
            history.append((activity.timestamp, None))
        elif isinstance(activity, JnActivityStatusChanged):
            # check the old status to make sure it is consistent
            if len(history) > 0:
                if history[-1][1] is None:
                    history[-1] = (history[-1][0], activity.old_status)
                elif history[-1][1] != activity.old_status:
                    logger.warning(f"Job status history inconsistency detected: at {activity.timestamp}, the old status was {activity.old_status}, but the previous entry in the history was {history[-1][1]}")
            history.append((activity.timestamp, activity.new_status))
    return history

def update_job_status_histories(job_activities: dict[str, list[JnActivity]], out_job_status_histories: dict[str, list[(datetime, JobStatus)]]):
    """For each job in job_jnids, update the job status history in out_job_status_histories."""
    for job_jnid, activities in job_activities.items():
        out_job_status_histories[job_jnid] = construct_job_status_history(activities)
