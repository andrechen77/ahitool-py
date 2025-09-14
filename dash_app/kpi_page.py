from collections import defaultdict
import time
from dash import Input, Output, callback, dcc, html, dash_table
import logging
import job_nimbus as jn
from job_nimbus import JnActivity
from app_data import global_data as gd

logger = logging.getLogger(__name__)

kpi_layout = html.Div([
    html.H2("KPI Dashboard"),
    html.Div([
        dcc.Loading(children=[
            fetch_statuses_button := html.Button("Fetch Job Statuses", className="btn btn-primary", style={"margin": "5px"}),
            notify_job_statuses := dcc.Store(id="notify_job_statuses"),
        ]),
        dcc.Loading(children=[
            fetch_jnids_button := html.Button("Fetch Job JNIDs", className="btn btn-primary", style={"margin": "5px"}),
            notify_job_jnids := dcc.Store(id="notify_job_jnids"),
        ]),
        dcc.Loading(children=[
            fetch_activities_button := html.Button("Fetch Job Activities", className="btn btn-secondary", style={"margin": "5px"}),
            notify_job_activities := dcc.Store(id="notify_job_activities"),
        ]),
        dcc.Loading(children=[
            calculate_histories_button := html.Button("Calculate Status Histories", className="btn btn-success", style={"margin": "5px"}),
            notify_job_status_histories := dcc.Store(id="notify_job_status_histories"),
        ]),
        table := html.Div(),
    ]),
])

@callback(
    Output(notify_job_statuses, "data"),
    Input(fetch_statuses_button, "n_clicks"),
    prevent_initial_call=True
)
def fetch_job_statuses(n_clicks):
    if n_clicks is None:
        return "None"

    logger.info("Updating job statuses...")
    gd.jn_job_statuses.value = jn.api.request_job_statuses()
    logger.info(f"Updated job statuses for {len(gd.jn_job_statuses.value)} jobs")

    return time.time()

@callback(
    Output(notify_job_jnids, "data"),
    Input(fetch_jnids_button, "n_clicks"),
    prevent_initial_call=True
)
def fetch_jnids(n_clicks):
    if n_clicks is None:
        return "None"

    logger.info("Requesting all job JNIDs...")
    gd.jn_job_jnids.value = jn.api.request_all_job_jnids()
    logger.info(f"Retrieved {len(gd.jn_job_jnids.value)} job JNIDs")

    return time.time()

@callback(
    Output(notify_job_activities, "data"),
    Input(fetch_activities_button, "n_clicks"),
    prevent_initial_call=True
)
def fetch_job_activities(n_clicks):
    if n_clicks is None:
        return "None"

    logger.info("Updating job activities...")
    job_activities = jn.api.request_all_job_activity()
    gd.jn_job_activities.value = [jn.parse_jn_activity(a) for a in job_activities]
    logger.info(f"Updated job activities for {len(gd.jn_job_activities.value)} jobs")

    return time.time()

@callback(
    Output(notify_job_status_histories, "data"),
    Input(calculate_histories_button, "n_clicks"),
    prevent_initial_call=True
)
def calculate_status_histories(n_clicks):
    if n_clicks is None:
        return "None"

    logger.info("Updating job status histories...")
    activities_by_job: dict[str, list['JnActivity']] = defaultdict(list)
    for activity in gd.jn_job_activities.value:
        activities_by_job[activity.primary_jnid].append(activity)
    gd.jn_job_status_histories.value = {
        job_jnid: jn.construct_job_status_history(activities)
        for job_jnid, activities in activities_by_job.items()
    }
    logger.info(f"Updated status histories for {len(gd.jn_job_status_histories.value)} jobs")

    return time.time()

@callback(
    Output(table, "children"),
    Input(notify_job_status_histories, "data")
)
def update_jnid_list(data):
    if data is None:
        logger.info("No data to display in JNID list")
        return "No data to display."

    logger.info("Updating JNID list display")
    table_data = []
    for jnid, history in gd.jn_job_status_histories.value.items():
        history_str = " -> ".join([
            f"{ts.strftime('%Y-%m-%d')}: {status.name if status else 'Created'}"
            for ts, status in history
        ])
        table_data.append({
            "Job ID": jnid,
            "Status History": history_str
        })

    logger.info(f"Created table with {len(table_data)} job entries")
    return html.Div([
        html.H4("Job Status Histories"),
        dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Job ID", "id": "Job ID"},
                {"name": "Status History", "id": "Status History"}
            ],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'height': 'auto',
            }
        )
    ])
