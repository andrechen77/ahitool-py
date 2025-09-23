# wrapper script for the dash_app.entry module

import logging
from threading import Timer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
# console_handler = logging.StreamHandler(sys.stdout)
# console_handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
# console_handler.setFormatter(formatter)
# root_logger = logging.getLogger()
# root_logger.setLevel(logging.INFO)
# root_logger.addHandler(console_handler)
# dash_logger = logging.getLogger('dash')
# dash_logger.setLevel(logging.INFO)
# dash_logger.addHandler(console_handler)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from dash_app.app import create_app, initialize_data

HOST = "127.0.0.1"
PORT = 8050

def open_browser():
    try:
        import webbrowser
        webbrowser.open(f"http://{HOST}:{PORT}")
        logger.info(f"Opened browser to http://{HOST}:{PORT}")
    except Exception as e:
        logger.error(f"Error opening browser: {e}")
        logger.info(f"Please open your browser and navigate to http://{HOST}:{PORT}")

# run the app
"""Entry point function to run the Dash GUI"""
logger.info("Starting Dash application...")
Timer(1, open_browser).start()
initialize_data()
app = create_app()
app.run(debug=False, host=HOST, port=PORT)
