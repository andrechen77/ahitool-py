from .base_data import JobStatus, JobLeadSource, parse_job_base_data, JobParsedBaseData
from .json_keys import KEY_JNID
from dataclasses import dataclass
from datetime import datetime
from typing import Any
import requests
import json
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Global session object for JobNimbus API requests
_session = None

def initialize_session(api_key: str):
    """Initialize the global session with the API key."""
    logger.info(f"Initializing session with API key: {api_key}")

    global _session
    _session = requests.Session()
    _session.headers.update({
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    })

def get_session() -> requests.Session:
    """Get the global session, initializing it if necessary."""
    if _session is None:
        raise RuntimeError("Session not initialized. Call initialize_session() first.")
    return _session

_status_registry = None
def set_status_registry(statuses: dict[int, JobStatus]):
    global _status_registry
    _status_registry = statuses

MAX_PER_REQUEST = 7000

def request_all_from_job_nimbus(path: str, results_key: str, filter_str: str = None, fields: list[str] = None) -> list[Any]:
    """
    Make a request to the JobNimbus API. The expected response is JSON with
    `{'count': int, '<results_key>': [...]}`. This function will make a request
    with size 0 to find the number of results, and then make a request for
    all results at once.
    """
    session = get_session()
    endpoint = f"https://app.jobnimbus.com/api1/{path}"
    params = {'size': str(0)}
    if filter_str:
        params['filter'] = filter_str
    if fields:
        params['fields'] = ','.join(fields)

    # make a request with size 0 to find the number of results
    # response = session.get(endpoint, params=params)
    # response.raise_for_status()
    # data = response.json()
    # if not isinstance(data, dict):
    #     raise ValueError("Invalid response format: not valid JSON")
    # if 'count' not in data:
    #     raise ValueError("Invalid response format: missing 'count' field")
    # total_num_results = data['count']

    # make a request for all results at once
    # results = []
    # while len(results) < total_num_results:
        # params['size'] = str(min(1000, total_num_results - len(results)))
        # params['from'] = str(len(results))
    # params['size'] = str(min(MAX_PER_REQUEST, total_num_results))
    params['size'] = str(MAX_PER_REQUEST)

    response = session.get(endpoint, params=params)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Invalid response format: not valid JSON")
    if results_key not in data:
        raise ValueError(f"Invalid response format: missing '{results_key}' field")
    return data[results_key]

    #     results.extend(data[results_key])
    #     total_num_results = data['count']

    #     logger.info(f"Retrieved {len(results)} of {total_num_results} results")

    # return results

def request_from_job_nimbus(path: str) -> Any:
    """
    Make a request to the JobNimbus API and return the JSON data.

    Args:
        path: API endpoint path

    Returns:
        The response data from the API

    Raises:
        requests.RequestException: If the API request fails
    """
    session = get_session()
    endpoint = f"https://app.jobnimbus.com/api1/{path}"

    try:
        response = session.get(endpoint)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API request failed: {e.response.status_code} {e.response.headers} {e.response.text}")
        raise e

def request_all_job_base_data(filter_str: str = None) -> dict[str, JobParsedBaseData]:
    jobs_json = request_all_from_job_nimbus("jobs", "results", filter_str)
    return {job_json[KEY_JNID]: parse_job_base_data(job_json, _status_registry) for job_json in jobs_json}

def request_all_job_jnids(filter_str: str = None) -> list[str]:
    results = request_all_from_job_nimbus("jobs", "results", filter_str, [KEY_JNID])
    return [result[KEY_JNID] for result in results]

def request_job_activity_for_job(job_jnid: str) -> list[dict[str, Any]]:
    """
    Request all activities for a job.

    Returns: A list of JSON dicts, each of which represents a status change
    for the job.
    """
    filter_str = json.dumps({
        "must": [
            {
                "term": {
                    "primary.id": job_jnid,
                },
            },
            {
                "term": {
                    "is_status_change": True,
                }
            }
        ]
    })
    return request_all_from_job_nimbus(f"activities", "activity", filter_str)

def request_all_job_activity() -> list[dict[str, Any]]:
    filter_str = json.dumps({
        "must": [
            {
                "term": {
                    "is_status_change": True,
                },
            },
            {
                "term": {
                    "primary.type": "job"
                }
            }
        ]
    })

    earliest_ts = None
    activities = []
    while True:
        new_activities = request_all_from_job_nimbus(f"activities", "activity", filter_str)
        logger.debug(f"Retrieved {len(new_activities)} activities")
        activities.extend(new_activities)
        if len(new_activities) < MAX_PER_REQUEST:
            break
        earliest_ts = activities[-1]['date_created']
        logger.debug(f"Earliest timestamp: {datetime.fromtimestamp(earliest_ts)}")

        filter_str = json.dumps({
            "must": [
                {
                    "term": {
                        "is_status_change": True,
                    },
                },
                {
                    "range": {
                        "date_created": {
                            "lte": earliest_ts,
                        }
                    }
                },
            ]
        })

    deduped = list({a["jnid"]: a for a in activities}.values())
    return deduped

def request_job_statuses() -> dict[int, JobStatus]:
    logger.info("Requesting job statuses...")
    # get the settings object
    settings = request_from_job_nimbus("account/settings")
    logger.debug(f"Settings gotten")

    # find the workflow for jobs in JobNimbus settings
    job_workflows = [w for w in settings['workflows'] if w['object_type'] == 'job']
    logger.debug(f"Found job workflows {[w['name'] for w in job_workflows]}")
    statuses = {}
    for job_workflow in job_workflows:
        for status in job_workflow['status']:
            new_status = JobStatus(status['id'], status['name'])
            statuses[new_status.id] = new_status
            logger.debug(f"Added status from workflow {job_workflow['name']}: {new_status.name} with id {new_status.id}")
    return statuses

def request_lead_sources() -> dict[int, JobLeadSource]:
    # get the settings object
    settings = request_from_job_nimbus("account/settings")

    sources = {}
    for source in settings['sources']:
        source_id = int(source['JobSourceId'])
        name = source['SourceName']
        sources[source_id] = JobLeadSource(source_id, name)
    return sources

def request_put(path: str, json: dict[str, Any]) -> Any:
    session = get_session()
    endpoint = f"https://app.jobnimbus.com/api1/{path}"

    # confirmation = input(f"Proceed with PUT {endpoint} with json {json}? (Y/N): ")
    # if confirmation.strip().upper() != "Y":
    #     print("Request cancelled")
    #     return None

    try:
        print(f"PUT {endpoint} with json {json}")
        response = session.put(endpoint, json=json)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise requests.RequestException(f"API request failed: {e}")

def request_update_job_base_data(job_jnid: str, json: dict[str, Any]):
    request_put(f"jobs/{job_jnid}", json)

