import os
import os.path

from config import logger

# TODO googletrans

def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
        logger.info(f"Creating {os.path.basename(path)} folder.")
        return True
    else:
        assert os.path.isdir(path)
        return False

