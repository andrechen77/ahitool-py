from dash import Dash, html, callback, Output, Input, dcc
import dash_bootstrap_components as dbc
from .kpi_page import kpi_layout
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app_layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(
                dbc.NavLink("KPIs", href="/kpis", active="exact")
            ),
        ],
        brand="ahitool",
        brand_href="/",
        color="primary",
        dark=True,
        className="mb-4",
    ),
    html.Div(id='page-content')
], fluid=True)

home_layout = html.Div([
    html.H1("Welcome to AHI Tool", className="text-center mb-4"),
    html.P("Select an option from the navigation bar above.", className="text-center text-muted")
])

not_found_layout = html.Div([
    html.H1("404: Not found", className="text-danger"),
    html.P(f"This URL is not valid. Please check the URL and try again.")
])

# Render page content based on the URL
@callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def render_page_content(pathname):
    logger.info(f"Rendering page content for pathname: {pathname}")
    match pathname:
        case "/kpis":
            logger.info("Loading KPI dashboard page")
            return kpi_layout
        case "/":
            logger.info("Loading home page")
            return home_layout
        case _:
            logger.warning(f"Page not found: {pathname}")
            return not_found_layout
