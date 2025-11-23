from qgis.core import QgsProcessingProvider

# Import algorithms
from .underground.river_channel_algorithm import RiverChannelAlgorithm
from .underground.banklines_algorithm import BanklinesAlgorithm
from .underground.floodzone_algorithm import FloodZoneAlgorithm
from .underground.watershed_zones_algorithm import WatershedZonesAlgorithm

from .erosion.erosion_algorithm import ErosionAlgorithm
from .weathering.weathering_algorithm import WeatheringAlgorithm


class EcosystemProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        """Register all algorithms."""
        self.addAlgorithm(RiverChannelAlgorithm())
        self.addAlgorithm(BanklinesAlgorithm())
        self.addAlgorithm(FloodZoneAlgorithm())
        self.addAlgorithm(WatershedZonesAlgorithm())

        self.addAlgorithm(ErosionAlgorithm())
        self.addAlgorithm(WeatheringAlgorithm())

    def id(self):
        return "ecosystem_toolkit"

    def name(self):
        return "Ecosystem Toolkit"

    def longName(self):
        return "Underground Ecosystem Toolkit"

    def initGui(self):
        pass

    def unload(self):
        pass
