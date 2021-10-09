import logging
import sys


logger = logging.getLogger('bcnetwork')
logger.addHandler(
    logging.StreamHandler(stream=sys.stderr)
)
logger.setLevel('ERROR')
