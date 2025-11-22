from __future__ import annotations

from pathlib import Path

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
)

from src.underground.config import UndergroundCostWeights, UndergroundInputs
from src.underground.cost_builder import build_cost_raster


class BuildUndergroundCostAlgorithm(QgsProcessingAlgorithm):
    INPUT_DEM = "INPUT_DEM"
    INPUT_GW = "INPUT_GW"
    INPUT_PERMEABILITY = "INPUT_PERMEABILITY"
    INPUT_KARST = "INPUT_KARST"
    OUTPUT_COST = "OUTPUT_COST"
    WEIGHT_SLOPE = "WEIGHT_SLOPE"
    WEIGHT_PERM = "WEIGHT_PERM"
    WEIGHT_KARST = "WEIGHT_KARST"

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_DEM, "DEM (GeoTIFF)")
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_GW, "Groundwater surface (GeoTIFF)"
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_PERMEABILITY, "Permeability raster (GeoTIFF)"
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_KARST, "Karst index raster (GeoTIFF)"
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.WEIGHT_SLOPE, "Slope weight", type=QgsProcessingParameterNumber.Double, defaultValue=0.4, minValue=0, maxValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.WEIGHT_PERM, "Permeability weight", type=QgsProcessingParameterNumber.Double, defaultValue=0.25, minValue=0, maxValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.WEIGHT_KARST, "Karst weight", type=QgsProcessingParameterNumber.Double, defaultValue=0.2, minValue=0, maxValue=1
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_COST, "Cost raster", fileFilter="GeoTIFF (*.tif)"
            )
        )

    def processAlgorithm(
        self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ):
        dem_layer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        gw_layer = self.parameterAsRasterLayer(parameters, self.INPUT_GW, context)
        perm_layer = self.parameterAsRasterLayer(parameters, self.INPUT_PERMEABILITY, context)
        karst_layer = self.parameterAsRasterLayer(parameters, self.INPUT_KARST, context)
        slope_weight = self.parameterAsDouble(parameters, self.WEIGHT_SLOPE, context)
        perm_weight = self.parameterAsDouble(parameters, self.WEIGHT_PERM, context)
        karst_weight = self.parameterAsDouble(parameters, self.WEIGHT_KARST, context)

        depth_weight = max(0.0, 1.0 - slope_weight - perm_weight - karst_weight)

        output_path = Path(
            self.parameterAsFileOutput(parameters, self.OUTPUT_COST, context)
        )

        inputs = UndergroundInputs(
            dem_path=Path(dem_layer.source()),
            groundwater_path=Path(gw_layer.source()),
            permeability_path=Path(perm_layer.source()),
            karst_path=Path(karst_layer.source()),
            source_points_path=Path(),
            outlet_points_path=Path(),
        )
        weights = UndergroundCostWeights(
            slope=slope_weight,
            permeability=perm_weight,
            karst=karst_weight,
            depth=depth_weight,
        )
        build_cost_raster(inputs, weights, output_path)
        feedback.pushInfo(f"Слой стоимости сохранён в {output_path}")
        return {self.OUTPUT_COST: str(output_path)}

    def name(self) -> str:
        return "build_underground_cost"

    def displayName(self) -> str:
        return "Построить слой стоимости подземных потоков"

    def group(self) -> str:
        return "Underground"

    def groupId(self) -> str:
        return "underground"

