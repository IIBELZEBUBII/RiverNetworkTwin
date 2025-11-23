from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFileDestination,
    QgsRasterLayer,
    QgsFields,
    QgsField,
    QgsFeature,
    QgsVectorFileWriter,
    QgsGeometry,
    QgsWkbTypes,
    QgsProcessingException
)
from qgis.PyQt.QtCore import QVariant
import numpy as np

from ..utils.terrain import raster_to_array, raster_origin, raster_pixel_size
from ..utils.geometry import pixel_to_map


class BanklinesAlgorithm(QgsProcessingAlgorithm):

    INPUT_DEM = "INPUT_DEM"
    OUTPUT = "OUTPUT"

    def createInstance(self):
        return BanklinesAlgorithm()

    def name(self):
        return "banklines"

    def displayName(self):
        return "Extract River Banklines"

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
                "Output Banklines",
                "Shapefile (*.shp)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        dem_layer: QgsRasterLayer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem_layer is None:
            raise QgsProcessingException("DEM not loaded.")

        arr = raster_to_array(dem_layer)
        ox, oy = raster_origin(dem_layer)
        pw, ph = raster_pixel_size(dem_layer)

        feedback.pushInfo("Computing slope...")

        gy, gx = np.gradient(arr.astype(float))
        slope_mag = np.sqrt(gx**2 + gy**2)

        threshold = np.percentile(slope_mag, 95)
        mask = slope_mag > threshold

        rows, cols = np.where(mask)
        points = [pixel_to_map(ox, oy, pw, ph, r, c) for r, c in zip(rows, cols)]

        if not points:
            raise QgsProcessingException("No bankline points detected.")

        out_path = self.parameterAsFile(parameters, self.OUTPUT, context)

        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))

        writer = QgsVectorFileWriter(
            out_path,                    # file path
            "UTF-8",                     # encoding
            fields,                      # fields
            QgsWkbTypes.MultiPoint,      # geometry type
            dem_layer.crs(),             # CRS
            "ESRI Shapefile"             # driver name
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise QgsProcessingException("Writer error: " + writer.errorMessage())

        feat = QgsFeature()
        feat.setFields(fields)
        feat.setAttribute("id", 1)
        feat.setGeometry(QgsGeometry.fromMultiPointXY(points))
        writer.addFeature(feat)

        del writer

        feedback.pushInfo("Banklines extraction complete.")
        return {self.OUTPUT: out_path}