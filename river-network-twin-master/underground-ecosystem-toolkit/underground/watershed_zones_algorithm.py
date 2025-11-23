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


class WatershedZonesAlgorithm(QgsProcessingAlgorithm):

    INPUT_DEM = "INPUT_DEM"
    OUTPUT = "OUTPUT"

    def name(self):
        return "watershed_zones"

    def displayName(self):
        return "Watershed Zones"

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
                "Output Watershed Zones",
                "Shapefile (*.shp)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        arr = raster_to_array(dem)

        feedback.pushInfo("Computing slope to detect watershed ridge zones...")

        gy, gx = np.gradient(arr)
        slope = np.sqrt(gx * gx + gy * gy)

        cutoff = np.percentile(slope, 5)
        mask = slope <= cutoff

        ox, oy = raster_origin(dem)
        pw, ph = raster_pixel_size(dem)

        rows, cols = np.where(mask)

        pts = []
        for r, c in zip(rows, cols):
            x = ox + c * pw
            y = oy - r * abs(ph)
            pts.append(QgsPointXY(x, y))

        geom = QgsGeometry.fromMultiPointXY(pts)

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

        feedback.pushInfo("Watershed ridge zone extraction completed.")

        return {self.OUTPUT: out_path}

    def createInstance(self):
        return WatershedZonesAlgorithm()