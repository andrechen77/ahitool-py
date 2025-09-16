# wrapper script for the dash_app.entry module

from dash_app.entry import run
import job_nimbus as jn
from app_data import global_data as gd
import logging
import sys

# set up logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)
dash_logger = logging.getLogger('dash')
dash_logger.setLevel(logging.INFO)
dash_logger.addHandler(console_handler)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# initialize data
jn.api.initialize_session(gd.jn_api_key.value)
jn.api.set_status_registry(gd.jn_job_statuses.value)

# run the app
run()
