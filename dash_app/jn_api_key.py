import logging
import job_nimbus as jn
from app_data import global_data as gd
from dash import html, Input, callback, dcc
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

layout = dbc.Row([
    dbc.Col(html.P("JobNimbus API Key"), width="auto"),
    dbc.Col(dbc.Input(id="jn_api_key", type="password", value=gd.jn_api_key.value, debounce=True), width="auto"),
])

@callback(
    Input("jn_api_key", "value"),
    prevent_initial_call=True
)
def update_jn_api_key(jn_api_key):
    gd.jn_api_key.value = jn_api_key
    jn.api.initialize_session(jn_api_key)

