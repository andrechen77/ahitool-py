from collections import defaultdict
import time
from dash import Input, Output, callback, dcc, html, dash_table, State
import logging
from job_analysis.graph_embedding import JobGraphEmbedding
import job_nimbus as jn
from job_nimbus import JnActivity
from app_data import global_data as gd
import plotly.graph_objects as go
import dash_app.jn_api_key as jn_api_key

logger = logging.getLogger(__name__)

kpi_layout = html.Div([
    html.H2("KPI Dashboard"),
    jn_api_key.layout,
    html.Div([
        dcc.Loading(children=[
            fetch_statuses_button := html.Button("Fetch Job Statuses", className="btn btn-primary", style={"margin": "5px"}),
            notify_job_statuses := dcc.Store(id="notify_job_statuses"),
        ]),
        dcc.Loading(children=[
            fetch_base_data_button := html.Button("Fetch Job Base Data", className="btn btn-primary", style={"margin": "5px"}),
            notify_job_base_data := dcc.Store(id="notify_job_base_data"),
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
    html.Div([
        graph_settings_input := dcc.Textarea(
            placeholder='Enter text here...',
            style={'margin': '5px', 'width': '100%', 'height': '150px'},
        ),
        generate_graph_button := html.Button(
            'Generate Graph',
            className='btn btn-primary',
            style={'margin': '5px'}
        ),
        graph_div := dcc.Graph()
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
    jn.api.set_status_registry(gd.jn_job_statuses.value)
    logger.info(f"Updated job statuses for {len(gd.jn_job_statuses.value)} jobs")

    return time.time()

@callback(
    Output(notify_job_base_data, "data"),
    Input(fetch_base_data_button, "n_clicks"),
    prevent_initial_call=True
)
def fetch_base_data(n_clicks):
    if n_clicks is None:
        return "None"

    logger.info("Requesting all job base data...")
    gd.jn_job_base_data.value = jn.api.request_all_job_base_data()
    logger.info(f"Retrieved {len(gd.jn_job_base_data.value)} job base data")

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
        job_jnid: jn.construct_job_status_history(activities, gd.jn_job_base_data.value[job_jnid].status)
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

@callback(
    Output(graph_div, "figure"),
    Input(generate_graph_button, "n_clicks"),
    State(graph_settings_input, "value"),
    prevent_initial_call=True
)
def generate_graph(n_clicks, graph_settings):
    if n_clicks is None:
        return "No graph generated"

    logger.info(f"Generating graph with settings: {repr(graph_settings)}")

    if graph_settings is None:
        return "No graph settings provided"

    # group jobs by status name
    status_by_name = defaultdict(set)
    for job_id, status in gd.jn_job_statuses.value.items():
        if status and status.name:
            status_by_name[status.name].add(status)

    # Split settings into rows, then split each row by commas
    assert isinstance(graph_settings, str)
    status_groups = []
    status_group_nicknames = []
    invalid_status_names = []
    for row in graph_settings.strip().split('\n'):
        status_group = set()
        split = row.split(':', 1)
        if len(split) == 2:
            nickname = split[0].strip()
            row = split[1].strip()
        else:
            nickname = row
        for name in row.strip().split(','):
            name = name.strip()
            if name in status_by_name:
                status_group.update(status_by_name[name])
            else:
                invalid_status_names.append(name)
        status_groups.append(frozenset(status_group))
        status_group_nicknames.append(nickname)
    logger.info(f"Status groups: {status_groups}")
    if invalid_status_names:
        logger.warning(f"Invalid status names: {', '.join(invalid_status_names)}")

    # add all jobs to the embedding
    graph_embedding = JobGraphEmbedding(status_groups, remove_cycles=False)
    invisible_jobs = []
    for job_id, status_history in gd.jn_job_status_histories.value.items():
        added_edges = graph_embedding.add_status_history(status_history)
        if added_edges == 0:
            invisible_jobs.append(job_id)
    if invisible_jobs:
        logger.warning(f"{len(invisible_jobs)} jobs are invisible: {', '.join(invisible_jobs[:100])}")

    # convert to sankey diagram
    labels = [*status_group_nicknames, "Job Created"]
    source_indices, target_indices, values, avg_duration = graph_embedding.to_sankey()
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="lightblue"
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values,
            customdata=avg_duration,
            hovertemplate="%{source.label} -> %{target.label}<br>Average duration: %{customdata}"
        )
    )])
    fig.update_layout(
        title_text="Job Status Flow Diagram",
        font_size=10,
        height=800
    )
    logger.info(f"Generated graph with labels {[*status_group_nicknames, 'Job Created']}")
    return fig