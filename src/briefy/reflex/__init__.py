"""briefy.reflex."""
from briefy import common
from briefy import gdrive
from briefy import reflex
from zope.configuration.xmlconfig import XMLConfig

import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

cs = logging.StreamHandler()
cs.setLevel(logging.INFO)
logger.addHandler(cs)


XMLConfig('configure.zcml', common)()
XMLConfig('configure.zcml', gdrive)()
XMLConfig('configure.zcml', reflex)()
