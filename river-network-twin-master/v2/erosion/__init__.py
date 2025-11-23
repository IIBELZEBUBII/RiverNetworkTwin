# __init__.py

def classFactory(iface):
    from .provider import EcosystemProvider
    return EcosystemProvider()