from app.cli.cli import main
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Explicitly configure the logger for app.api.client
client_logger = logging.getLogger("app.api.client")
client_logger.setLevel(logging.INFO)
