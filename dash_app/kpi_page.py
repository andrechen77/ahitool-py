from collections import defaultdict
import time
from dash import Input, Output, callback, dcc, html, dash_table, State
import dash_bootstrap_components as dbc
import logging
from job_analysis.graph_embedding import JobGraphEmbedding
import job_nimbus as jn
from job_nimbus import JnActivity
from app_data import global_data as gd
import plotly.graph_objects as go
import dash_app.jn_client as jn_client

logger = logging.getLogger(__name__)

kpi_layout = html.Div([
    html.H2("KPI Dashboard"),
    jn_client.layout,
    dbc.Card([
        dbc.CardHeader("Job Status Histories"),
        dbc.CardBody([
            dbc.Textarea(
                id="graph-settings-input",
                placeholder='Category A: Status 1, Status 2, Status 3\nCategory B: Status 4, Status 5, Status 6\netc...',
                rows=5,
                value=gd.kpi_graph_settings.val or "",
            ),
            dbc.Button(
                "Generate Graph",
                id="generate-graph-button",
            ),
            dcc.Graph(id="graph-output"),
        ])
    ]),
])

@callback(
    Output("graph-output", "figure"),
    Input("generate-graph-button", "n_clicks"),
    State("graph-settings-input", "value"),
    prevent_initial_call=True
)
def generate_graph(n_clicks, graph_settings):
    if n_clicks is None:
        return "No graph generated"

    logger.info(f"Generating graph with settings: {repr(graph_settings)}")

    if graph_settings is None:
        return "No graph settings provided"

    gd.kpi_graph_settings.val = graph_settings

    # group jobs by status name
    status_by_name = defaultdict(set)
    for job_id, status in gd.jn_job_statuses.val.items():
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

    # construct job status histories from activities
    activities_by_job = defaultdict(list)
    for activity in gd.jn_job_activities.val:
        activities_by_job[activity.primary_jnid].append(activity)
    job_status_histories = {
        job_jnid: jn.construct_job_status_history(activities, gd.jn_job_base_data.val[job_jnid].status)
        for job_jnid, activities in activities_by_job.items() if job_jnid in gd.jn_job_base_data.val
    }

    # add all jobs to the embedding
    graph_embedding = JobGraphEmbedding(status_groups, remove_cycles=False)
    invisible_jobs = []
    for job_id, status_history in job_status_histories.items():
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