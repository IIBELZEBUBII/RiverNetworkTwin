from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFileDestination,
    QgsGeometry, QgsFields, QgsField, QgsFeature,
    QgsVectorFileWriter, QgsWkbTypes
)
from qgis.PyQt.QtCore import QVariant
import numpy as np

from ..utils.terrain import raster_to_array, raster_origin, raster_pixel_size
from ..utils.geometry import pixel_to_map


class WeatheringAlgorithm(QgsProcessingAlgorithm):

    INPUT_DEM = "INPUT_DEM"
    OUTPUT = "OUTPUT"

    def name(self):
        return "weathering_zones"

    def displayName(self):
        return "Sediment Weathering Zones"

    def group(self):
        return "Ecosystem"

    def groupId(self):
        return "ecosystem"

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
                "Output Weathering Zones",
                "Shapefile (*.shp)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        arr = raster_to_array(dem)

        gy, gx = np.gradient(arr)
        gyy, gyx = np.gradient(gy)
        gxy, gxx = np.gradient(gx)
        curvature = gxx + gyy

        mask = curvature <= np.percentile(curvature, 5)

        ox, oy = raster_origin(dem)
        pw, ph = raster_pixel_size(dem)

        pts = []
        for r in range(arr.shape[0]):
            for c in range(arr.shape[1]):
                if mask[r, c]:
                    pts.append(pixel_to_map(ox, oy, pw, ph, r, c))

        geom = QgsGeometry.fromMultiPointXY(pts)

        fs = QgsFields()
        fs.append(QgsField("id", QVariant.Int))

        options = QgsVectorFileWriter.SaveVectorOptions()
        transform_context = context.transformContext()

        writer = QgsVectorFileWriter.create(
            parameters[self.OUTPUT],
            fs,
            QgsWkbTypes.MultiPoint,
            dem.crs(),
            transform_context,
            options
        )

        f = QgsFeature()
        f.setFields(fs)
        f.setAttribute("id", 1)
        f.setGeometry(geom)
        writer.addFeature(f)
        del writer

        return {self.OUTPUT: parameters[self.OUTPUT]}

    def createInstance(self):
        return WeatheringAlgorithm()