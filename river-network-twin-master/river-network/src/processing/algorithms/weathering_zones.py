from __future__ import annotations

from pathlib import Path

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterVectorDestination,
)

import processing

from src.weathering.analysis import build_weathering_mask, compute_weathering_index
from src.weathering.config import WeatheringInputs


class WeatheringZonesAlgorithm(QgsProcessingAlgorithm):
    BASIN = "BASIN"
    SLOPE = "SLOPE"
    MOISTURE = "MOISTURE"
    LITHOLOGY = "LITHOLOGY"
    TEMPERATURE = "TEMPERATURE"
    PERCENTILE = "PERCENTILE"
    OUTPUT_INDEX = "OUTPUT_INDEX"
    OUTPUT_VECTOR = "OUTPUT_VECTOR"

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(QgsProcessingParameterVectorLayer(self.BASIN, "Watershed polygons"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.SLOPE, "Slope raster"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.MOISTURE, "Moisture raster"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.LITHOLOGY, "Lithology index raster"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.TEMPERATURE, "Temperature amplitude raster"))
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PERCENTILE,
                "Percentile threshold",
                type=QgsProcessingParameterNumber.Double,
                defaultValue=85.0,
                minValue=50.0,
                maxValue=99.9,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_INDEX, "Weathering index raster", fileFilter="GeoTIFF (*.tif)"
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT_VECTOR, "Weathering polygons", type=QgsProcessingParameterVectorDestination.Polygon
            )
        )

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        basin = self.parameterAsVectorLayer(parameters, self.BASIN, context)
        slope = self.parameterAsRasterLayer(parameters, self.SLOPE, context)
        moisture = self.parameterAsRasterLayer(parameters, self.MOISTURE, context)
        lithology = self.parameterAsRasterLayer(parameters, self.LITHOLOGY, context)
        temperature = self.parameterAsRasterLayer(parameters, self.TEMPERATURE, context)
        percentile = self.parameterAsDouble(parameters, self.PERCENTILE, context)
        index_output = Path(self.parameterAsFileOutput(parameters, self.OUTPUT_INDEX, context))
        vector_output = self.parameterAsOutputLayer(parameters, self.OUTPUT_VECTOR, context)

        inputs = WeatheringInputs(
            watershed_path=Path(basin.source()),
            slope_path=Path(slope.source()),
            moisture_path=Path(moisture.source()),
            lithology_path=Path(lithology.source()),
            temperature_path=Path(temperature.source()),
        )

        feedback.pushInfo("Расчёт индекса выветривания")
        index_raster = compute_weathering_index(inputs, index_output)
        mask = build_weathering_mask(
            index_raster, percentile, Path(str(index_output).replace(".tif", "_mask.tif"))
        )
        feedback.pushInfo("Выделение зон и пересечение с водоразделами")
        polygons = processing.run(
            "gdal:polygonize",
            {"INPUT": str(mask), "BAND": 1, "FIELD": "weather", "OUTPUT": "TEMPORARY_OUTPUT"},
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        intersection = processing.run(
            "native:intersection",
            {
                "INPUT": basin,
                "OVERLAY": polygons,
                "INPUT_FIELDS": [],
                "OVERLAY_FIELDS": [],
                "OUTPUT": vector_output,
            },
            context=context,
            feedback=feedback,
        )["OUTPUT"]
        return {
            self.OUTPUT_INDEX: str(index_raster),
            self.OUTPUT_VECTOR: intersection,
        }

    def name(self) -> str:
        return "weathering_zones"

    def displayName(self) -> str:
        return "Зоны выветривания на водоразделах"

    def group(self) -> str:
        return "Hazard"

    def groupId(self) -> str:
        return "hazard"

