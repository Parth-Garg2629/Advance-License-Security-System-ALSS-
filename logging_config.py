import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging(app):
    """
    Configure rotating file logging for ALSS.
    Log file: <project_root>/logs/alss.log
    """
    log_dir = os.path.join(app.root_path, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, "alss.log")

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,   # ~1 MB
        backupCount=5,        # keep last 5 log files
    )
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
