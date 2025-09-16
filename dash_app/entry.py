import dash
import dash_bootstrap_components as dbc
from .app import app_layout
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def create_app():
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )
    app.layout = app_layout
    return app

def run():
    """Entry point function to run the Dash GUI"""
    logger.info("Starting Dash application...")
    app = create_app()
    app.run(debug=False, host='127.0.0.1', port=8050)
