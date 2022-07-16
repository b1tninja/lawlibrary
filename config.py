import logging
import os

data_dir = os.getenv('MOUNT_DIRECTORY', 'data')

logger = logging.getLogger()
logger.setLevel(logging.INFO)