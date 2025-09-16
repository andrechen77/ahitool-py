from .json_keys import KEY_JNID, KEY_STATUS_ID, KEY_STATUS_MOD_TIME, KEY_SALES_REP, KEY_INSURANCE_CHECKBOX, KEY_INSURANCE_COMPANY_NAME, KEY_INSURANCE_CLAIM_NUMBER, KEY_JOB_NUMBER, KEY_JOB_NAME, KEY_APPOINTMENT_DATE, KEY_CONTINGENCY_DATE, KEY_CONTRACT_DATE, KEY_INSTALL_DATE, KEY_LOSS_DATE, KEY_AMOUNT_RECEIVABLE
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class JobMilestone(Enum):
    """The important milestones that a job can be in."""
    LEAD_ACQUIRED = "Lead Acquired"
    APPOINTMENT_MADE = "Appointment Made"
    CONTINGENCY_SIGNED = "Contingency Signed"
    CONTRACT_SIGNED = "Contract Signed"
    INSTALLED = "Installed"
    LOST = "Lost"

@dataclass(frozen=True)
class JobStatus:
    id: int
    name: str

    # Global dictionary to store all JobStatus instances. This must be manually
    # populated and accessed.
    registry = {}

class JobInsuranceStatus(Enum):
    INSURANCE_WITH_CONTINGENCY = "Insurance With Contingency"
    INSURANCE_WITHOUT_CONTINGENCY = "Insurance Without Contingency"
    RETAIL = "Retail"

@dataclass
class MilestoneDates:
    """Container for milestone dates."""
    appointment_date: Optional[datetime] = None
    contingency_date: Optional[datetime] = None
    contract_date: Optional[datetime] = None
    install_date: Optional[datetime] = None
    loss_date: Optional[datetime] = None

    def __getitem__(self, milestone: JobMilestone) -> Optional[datetime]:
        """Get date for a specific milestone."""
        match milestone:
            case JobMilestone.LEAD_ACQUIRED:
                return None
            case JobMilestone.APPOINTMENT_MADE:
                return self.appointment_date
            case JobMilestone.CONTINGENCY_SIGNED:
                return self.contingency_date
            case JobMilestone.CONTRACT_SIGNED:
                return self.contract_date
            case JobMilestone.INSTALLED:
                return self.install_date
            case JobMilestone.LOST:
                return self.loss_date
            case _:
                raise KeyError(f"Unknown milestone: {milestone}")

@dataclass(frozen=True)
class JobLeadSource:
    id: int
    name: str

    # Global dictionary to store all JobLeadSource instances. This must be
    # manually populated and accessed.
    registry = {}

@dataclass
class JobParsedBaseData:
    jnid: str
    milestone_dates: MilestoneDates
    status: JobStatus
    status_mod_date: Optional[datetime]
    sales_rep: Optional[str]
    insurance_checkbox: bool
    insurance_claim_number: Optional[str]
    insurance_company_name: Optional[str]
    job_number: Optional[str]
    job_name: Optional[str]
    amt_receivable: int # amount in cents

def parse_job_base_data(raw_base_data: dict[str, Any], statuses: dict[int, JobStatus]) -> 'JobParsedBaseData':
    """
    Construct a Job object from JobNimbus API JSON response data.

    Args:
        data: Dictionary containing job data from JobNimbus API

    Returns:
        Job object with parsed data

    Raises:
        ValueError: If required fields are missing or invalid
    """
    def get_nonempty_string(key: str) -> str | None:
        value = raw_base_data.get(key)
        if isinstance(value, str) and value.strip():
            return value
        return None

    def get_timestamp_nonzero(key: str) -> datetime | None:
        value = raw_base_data.get(key)
        if isinstance(value, (int, float)) and value != 0:
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                return None
        return None

    # get the jnid
    jnid = raw_base_data.get(KEY_JNID)
    if not isinstance(jnid, str):
        raise ValueError(f"Missing or invalid {KEY_JNID} field")

    # get the job status
    status_id = raw_base_data.get(KEY_STATUS_ID)
    if status_id is None:
        raise ValueError(f"Missing or invalid {KEY_STATUS_ID} field")
    status = statuses[status_id]

    # get the last status update
    status_mod_date = get_timestamp_nonzero(KEY_STATUS_MOD_TIME)

    # optional fields
    sales_rep = get_nonempty_string(KEY_SALES_REP)
    insurance_checkbox = raw_base_data.get(KEY_INSURANCE_CHECKBOX, False)
    insurance_company_name = get_nonempty_string(KEY_INSURANCE_COMPANY_NAME)
    insurance_claim_number = get_nonempty_string(KEY_INSURANCE_CLAIM_NUMBER)
    job_number = get_nonempty_string(KEY_JOB_NUMBER)
    job_name = get_nonempty_string(KEY_JOB_NAME)

    # get the amount receivable
    amt_receivable = 0
    amount_value = raw_base_data.get(KEY_AMOUNT_RECEIVABLE)
    if isinstance(amount_value, (int, float)):
        amt_receivable = int(amount_value * 100)

    # get milestone dates
    milestone_dates = MilestoneDates(
        appointment_date=get_timestamp_nonzero(KEY_APPOINTMENT_DATE),
        contingency_date=get_timestamp_nonzero(KEY_CONTINGENCY_DATE),
        contract_date=get_timestamp_nonzero(KEY_CONTRACT_DATE),
        install_date=get_timestamp_nonzero(KEY_INSTALL_DATE),
        loss_date=get_timestamp_nonzero(KEY_LOSS_DATE)
    )

    return JobParsedBaseData(
        jnid=jnid,
        milestone_dates=milestone_dates,
        status=status,
        status_mod_date=status_mod_date,
        sales_rep=sales_rep,
        insurance_checkbox=insurance_checkbox,
        insurance_claim_number=insurance_claim_number,
        insurance_company_name=insurance_company_name,
        job_number=job_number,
        job_name=job_name,
        amt_receivable=amt_receivable
    )

