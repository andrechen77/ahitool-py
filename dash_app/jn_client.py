from datetime import datetime
import logging
import time
import job_nimbus as jn
from app_data import global_data as gd
from dash import Output, html, Input, callback, dcc
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

layout = dbc.Card([
    dbc.CardHeader("JobNimbus Client"),
    dbc.CardBody([
        dbc.Row([
            dbc.Col(html.B("API Key"), width="auto"),
            dbc.Col(dbc.Input(
                id="jn_api_key",
                type="password",
                placeholder="Enter API Key (required)",
                value=gd.jn_api_key.val,
                debounce=True,
                className="me-2",
            ), width="auto"),
        ]),
        dbc.Row([
            dbc.Col(html.B("Job Status Dictionary"), width="auto"),
            dbc.Col(
                dcc.Loading(children=[
                    dbc.Button("Manual Refresh", id="fetch-job-statuses-button"),
                    dcc.Store(id="notify-job-statuses"),
                ]),
                width="auto",
            ),
            dbc.Col([
                html.P(id="last-updated-job-statuses"),
            ], width="auto"),
        ]),
        dbc.Row([
            dbc.Col(html.B("Job Base Data"), width="auto"),
            dbc.Col(
                dcc.Loading(children=[
                    dbc.Button("Manual Refresh", id="fetch-job-base-data-button"),
                    dcc.Store(id="notify-job-base-data"),
                ]),
                width="auto",
            ),
            dbc.Col([
                html.P(id="last-updated-job-base-data"),
            ], width="auto"),
        ]),
        dbc.Row([
            dbc.Col(html.B("Job Activities"), width="auto"),
            dbc.Col(
                dcc.Loading(children=[
                    dbc.Button("Manual Refresh", id="fetch-job-activities-button"),
                    dcc.Store(id="notify-job-activities"),
                ]),
                width="auto",
            ),
            dbc.Col([
                html.P(id="last-updated-job-activities"),
            ], width="auto"),
        ]),
    ])
])


@callback(
    Input("jn_api_key", "value"),
    prevent_initial_call=True
)
def update_jn_api_key(jn_api_key):
    gd.jn_api_key.val = jn_api_key
    jn.api.initialize_session(jn_api_key)


@callback(
    Output("notify-job-statuses", "data"),
    Input("fetch-job-statuses-button", "n_clicks"),
    prevent_initial_call=True
)
def fetch_job_statuses(n_clicks):
    gd.jn_job_statuses.refresh()
    return gd.jn_job_statuses.last_updated

@callback(
    Output("last-updated-job-statuses", "children"),
    Input("notify-job-statuses", "data"),
    Input("notify-job-base-data", "data"),
    Input("notify-job-activities", "data"),
)
def render_job_statuses_last_update(data, n_intervals, n_intervals_activities):
    last_updated = gd.jn_job_statuses.last_updated
    if last_updated is None:
        return "No data (auto fetching when needed)"
    return f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}"

@callback(
    Output("notify-job-base-data", "data"),
    Input("fetch-job-base-data-button", "n_clicks"),
    prevent_initial_call=True
)
def fetch_job_base_data(n_clicks):
    gd.jn_job_base_data.refresh()
    return gd.jn_job_base_data.last_updated

@callback(
    Output("last-updated-job-base-data", "children"),
    Input("notify-job-base-data", "data"),
)
def render_job_base_data_last_update(data):
    last_updated = gd.jn_job_base_data.last_updated
    if last_updated is None:
        return "No data (auto fetching when needed)"
    return f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}"

@callback(
    Output("notify-job-activities", "data"),
    Input("fetch-job-activities-button", "n_clicks"),
    prevent_initial_call=True
)
def fetch_job_activities(n_clicks):
    gd.jn_job_activities.refresh()
    return gd.jn_job_activities.last_updated

@callback(
    Output("last-updated-job-activities", "children"),
    Input("notify-job-activities", "data"),
)
def render_job_activities_last_update(data):
    last_updated = gd.jn_job_activities.last_updated
    if last_updated is None:
        return "No data (auto fetching when needed)"
    return f"Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
