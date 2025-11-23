from __future__ import annotations

from pathlib import Path

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFileDestination,
)
from qgis.core import QgsVectorLayer

import processing


class ProtectionZoneAlgorithm(QgsProcessingAlgorithm):
    INPUT_BASIN = "INPUT_BASIN"
    INPUT_RIVER = "INPUT_RIVER"
    SURFACE = "SURFACE_DISTANCE"
    SUBSURFACE = "SUBSURFACE_DISTANCE"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(
            QgsProcessingParameterVectorLayer(self.INPUT_BASIN, "Underground basins")
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(self.INPUT_RIVER, "River layer")
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SURFACE,
                "Surface buffer (m)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200,
                minValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.SUBSURFACE,
                "Subsurface buffer (m)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=500,
                minValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT, "Protection zones", fileFilter="GeoPackage (*.gpkg)"
            )
        )

    def processAlgorithm(
        self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ):
        basin_layer = self.parameterAsVectorLayer(parameters, self.INPUT_BASIN, context)
        river_layer = self.parameterAsVectorLayer(parameters, self.INPUT_RIVER, context)
        surface = self.parameterAsDouble(parameters, self.SURFACE, context)
        subsurface = self.parameterAsDouble(parameters, self.SUBSURFACE, context)
        output = Path(self.parameterAsFileOutput(parameters, self.OUTPUT, context))

        feedback.pushInfo("Расчёт буферов для защитных зон")
        surface_layer = processing.run(
            "native:buffer",
            {
                "INPUT": river_layer,
                "DISTANCE": surface,
                "SEGMENTS": 24,
                "END_CAP_STYLE": 0,
                "DISSOLVE": True,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        subsurface_layer = processing.run(
            "native:buffer",
            {
                "INPUT": basin_layer,
                "DISTANCE": subsurface,
                "SEGMENTS": 16,
                "END_CAP_STYLE": 0,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        merged = processing.run(
            "native:mergevectorlayers",
            {"LAYERS": [surface_layer, subsurface_layer], "CRS": basin_layer.crs(), "OUTPUT": "TEMPORARY_OUTPUT"},
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        fielded = processing.run(
            "native:fieldcalculator",
            {
                "INPUT": merged,
                "FIELD_NAME": "zone",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 32,
                "FORMULA": "CASE WHEN $id=0 THEN 'surface' ELSE 'subsurface' END",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        result = processing.run(
            "native:dissolve",
            {"INPUT": fielded, "FIELD": ["zone"], "OUTPUT": str(output)},
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        result.setName("Protection zones")
        feedback.pushInfo(f"Защитные зоны сохранены в {output}")
        return {self.OUTPUT: str(output)}

    def name(self) -> str:
        return "protection_zones"

    def displayName(self) -> str:
        return "Защитные зоны подземных рек"

    def group(self) -> str:
        return "Protection"

    def groupId(self) -> str:
        return "protection"

