from __future__ import annotations

from pathlib import Path

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsVectorLayer,
)
from src.underground.network import run_network_analysis
from src.underground.polygonizer import polygonize_paths


class UndergroundPathsAlgorithm(QgsProcessingAlgorithm):
    INPUT_COST = "INPUT_COST"
    INPUT_SOURCES = "INPUT_SOURCES"
    INPUT_SINKS = "INPUT_SINKS"
    OUTPUT_PATHS = "OUTPUT_PATHS"
    OUTPUT_BASINS = "OUTPUT_BASINS"

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT_COST, "Cost raster")
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(self.INPUT_SOURCES, "Source points")
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(self.INPUT_SINKS, "Outlet points")
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_PATHS, "Output LCP (GPKG)", fileFilter="GeoPackage (*.gpkg)"
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_BASINS, "Output basins (GPKG)", fileFilter="GeoPackage (*.gpkg)"
            )
        )

    def processAlgorithm(
        self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ):
        cost_layer = self.parameterAsRasterLayer(parameters, self.INPUT_COST, context)
        sources_layer = self.parameterAsVectorLayer(parameters, self.INPUT_SOURCES, context)
        sinks_layer = self.parameterAsVectorLayer(parameters, self.INPUT_SINKS, context)
        line_output = Path(self.parameterAsFileOutput(parameters, self.OUTPUT_PATHS, context))
        polygon_output = Path(self.parameterAsFileOutput(parameters, self.OUTPUT_BASINS, context))

        path_layer = run_network_analysis(
            Path(cost_layer.source()),
            sources_layer,
            sinks_layer,
            line_output,
            cost_layer.crs().authid(),
            progress=None,
        )
        polygon_layer = polygonize_paths(path_layer, polygon_output)
        feedback.pushInfo("Подземные пути и водоразделы построены.")
        return {
            self.OUTPUT_PATHS: path_layer.source(),
            self.OUTPUT_BASINS: polygon_layer.source(),
        }

    def name(self) -> str:
        return "underground_paths"

    def displayName(self) -> str:
        return "Пути подземного стока и водоразделы"

    def group(self) -> str:
        return "Underground"

    def groupId(self) -> str:
        return "underground"

