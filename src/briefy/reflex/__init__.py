"""briefy.reflex."""
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

cs = logging.StreamHandler()
cs.setLevel(logging.INFO)
logger.addHandler(cs)
