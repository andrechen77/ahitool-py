import dash
import dash_bootstrap_components as dbc
from .app import app_layout
import logging
import sys

# Configure logging to display in terminal
def setup_logging():
    """Configure logging to display in terminal"""
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Also configure dash logger
    dash_logger = logging.getLogger('dash')
    dash_logger.setLevel(logging.INFO)
    dash_logger.addHandler(console_handler)

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
    setup_logging()
    logging.info("Starting Dash application...")
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=8050)

if __name__ == '__main__':
    import job_nimbus as jn
    from app_data import global_data as gd
    jn.api.initialize_session(gd.jn_api_key.value)
    run()