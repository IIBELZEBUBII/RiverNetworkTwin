from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFileDestination,
    QgsGeometry,
    QgsPointXY,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsVectorFileWriter,
    QgsWkbTypes,
    QgsProcessingException
)
from qgis.PyQt.QtCore import QVariant
import numpy as np

from ..utils.terrain import raster_to_array, raster_origin, raster_pixel_size


class RiverChannelAlgorithm(QgsProcessingAlgorithm):

    INPUT_DEM = "INPUT_DEM"
    OUTPUT = "OUTPUT"

    def createInstance(self):
        return RiverChannelAlgorithm()

    def name(self):
        return "river_channel"

    def displayName(self):
        return "Underground River Extraction"

    def group(self):
        return "Underground Ecosystem"

    def groupId(self):
        return "underground_ecosystem"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM,
                "Input DEM"
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                "Output Underground River",
                "Shapefile (*.shp)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem is None:
            raise QgsProcessingException("DEM not loaded!")

        arr = raster_to_array(dem)
        ox, oy = raster_origin(dem)
        pw, ph = raster_pixel_size(dem)

        feedback.pushInfo("Extracting lowest 1% terrain as underground drainage...")

        cutoff = np.percentile(arr, 1)
        rows, cols = np.where(arr <= cutoff)

        points = []
        for r, c in zip(rows, cols):
            x = ox + c * pw
            y = oy - r * abs(ph)
            points.append(QgsPointXY(x, y))

        if not points:
            raise QgsProcessingException("No underground river pixels detected.")

        geom = QgsGeometry.fromMultiPointXY(points)

        out_path = self.parameterAsFile(parameters, self.OUTPUT, context)

        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))

        writer = QgsVectorFileWriter(
            out_path,
            "UTF-8",
            fields,
            QgsWkbTypes.MultiPoint,
            dem.crs(),
            "ESRI Shapefile"
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise QgsProcessingException("Writer error: " + writer.errorMessage())

        feat = QgsFeature()
        feat.setFields(fields)
        feat.setAttribute("id", 1)
        feat.setGeometry(geom)
        writer.addFeature(feat)

        del writer

        feedback.pushInfo("Underground river extraction completed successfully.")

        return {self.OUTPUT: out_path}

    def createInstance(self):
        return RiverChannelAlgorithm()
