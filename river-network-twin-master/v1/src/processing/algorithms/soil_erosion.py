from __future__ import annotations

from pathlib import Path

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorDestination,
)

from src.erosion.analysis import compute_rusle, create_risk_mask
from src.erosion.config import RusleInputs
import processing


class SoilErosionAlgorithm(QgsProcessingAlgorithm):
    RAINFALL = "RAINFALL"
    SOIL = "SOIL"
    SLOPE = "SLOPE"
    COVER = "COVER"
    SUPPORT = "SUPPORT"
    THRESHOLD = "THRESHOLD"
    OUTPUT_RASTER = "OUTPUT_RASTER"
    OUTPUT_ZONES = "OUTPUT_ZONES"

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(QgsProcessingParameterRasterLayer(self.RAINFALL, "Rainfall factor (R)"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.SOIL, "Soil erodibility (K)"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.SLOPE, "Slope length-steepness (LS)"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.COVER, "Cover management (C)"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.SUPPORT, "Support practice (P)"))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                "High risk threshold (t/ha/yr)",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.1,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_RASTER, "Soil loss raster", fileFilter="GeoTIFF (*.tif)"
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT_ZONES, "High-risk polygons", type=QgsProcessingParameterVectorDestination.Polygon
            )
        )

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        rainfall = self.parameterAsRasterLayer(parameters, self.RAINFALL, context)
        soil = self.parameterAsRasterLayer(parameters, self.SOIL, context)
        slope = self.parameterAsRasterLayer(parameters, self.SLOPE, context)
        cover = self.parameterAsRasterLayer(parameters, self.COVER, context)
        support = self.parameterAsRasterLayer(parameters, self.SUPPORT, context)
        threshold = self.parameterAsDouble(parameters, self.THRESHOLD, context)
        raster_output = Path(self.parameterAsFileOutput(parameters, self.OUTPUT_RASTER, context))
        vector_output = self.parameterAsOutputLayer(parameters, self.OUTPUT_ZONES, context)

        inputs = RusleInputs(
            rainfall_path=Path(rainfall.source()),
            soil_erodibility_path=Path(soil.source()),
            slope_length_path=Path(slope.source()),
            cover_management_path=Path(cover.source()),
            support_practice_path=Path(support.source()),
        )

        feedback.pushInfo("Расчёт RUSLE")
        ras = compute_rusle(inputs, raster_output)
        mask = create_risk_mask(
            ras, threshold, Path(str(raster_output).replace(".tif", "_mask.tif"))
        )
        feedback.pushInfo("Полигонализация зон риска")
        polygons = processing.run(
            "gdal:polygonize",
            {
                "INPUT": str(mask),
                "BAND": 1,
                "FIELD": "risk",
                "OUTPUT": vector_output,
            },
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        return {
            self.OUTPUT_RASTER: str(ras),
            self.OUTPUT_ZONES: polygons,
        }

    def name(self) -> str:
        return "soil_erosion"

    def displayName(self) -> str:
        return "Зоны риска эрозии (RUSLE)"

    def group(self) -> str:
        return "Hazard"

    def groupId(self) -> str:
        return "hazard"

