"""briefy.reflex."""
from zope.configuration.xmlconfig import XMLConfig

import logging
import briefy.common
import briefy.gdrive

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

cs = logging.StreamHandler()
cs.setLevel(logging.INFO)
logger.addHandler(cs)


XMLConfig('configure.zcml', briefy.common)()
XMLConfig('configure.zcml', briefy.gdrive)()
