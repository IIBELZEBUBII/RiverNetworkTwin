from qgis.core import QgsApplication
from .provider import EcosystemProvider

def classFactory(iface):
    """Required by QGIS but unused for processing plugins."""
    provider = EcosystemProvider()
    QgsApplication.processingRegistry().addProvider(provider)
    return provider