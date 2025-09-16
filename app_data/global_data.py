from datetime import datetime
from .data_interface import DataInterface

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from job_nimbus import JnActivity, JobLeadSource, JobStatus, JobParsedBaseData

jn_api_key = DataInterface[str]("jn_api_key.json", "")
jn_job_statuses = DataInterface[dict[int, 'JobStatus']]("jn_job_statuses.json", {})
jn_lead_sources = DataInterface[dict[int, 'JobLeadSource']]("jn_lead_sources.json", {})
jn_job_jnids = DataInterface[list[str]]("jn_job_jnids.json", [])
jn_job_base_data = DataInterface[dict[str, 'JobParsedBaseData']]("jn_job_base_data.json", {})
jn_job_activities = DataInterface[list['JnActivity']]("jn_job_activities.json", {})
jn_job_status_histories = DataInterface[dict[str, list[tuple[datetime, 'JobStatus']]]]("jn_job_status_histories.json", {})
