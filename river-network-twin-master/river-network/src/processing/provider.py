from qgis.core import QgsProcessingProvider

from .algorithms.build_underground_cost import BuildUndergroundCostAlgorithm
from .algorithms.protection_zone import ProtectionZoneAlgorithm
from .algorithms.soil_erosion import SoilErosionAlgorithm
from .algorithms.underground_paths import UndergroundPathsAlgorithm
from .algorithms.weathering_zones import WeatheringZonesAlgorithm


class RiverNetworkProvider(QgsProcessingProvider):
    def loadAlgorithms(self) -> None:
        self.addAlgorithm(BuildUndergroundCostAlgorithm())
        self.addAlgorithm(UndergroundPathsAlgorithm())
        self.addAlgorithm(ProtectionZoneAlgorithm())
        self.addAlgorithm(SoilErosionAlgorithm())
        self.addAlgorithm(WeatheringZonesAlgorithm())

    def id(self) -> str:
        return "rivernetwork"

    def name(self) -> str:
        return "River Network Twin"

    def longName(self) -> str:
        return self.name()

