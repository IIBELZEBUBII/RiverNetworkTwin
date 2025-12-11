from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFileDestination,
    QgsFeature,
    QgsGeometry,
    QgsFields,
    QgsField,
    QgsVectorFileWriter,
    QgsWkbTypes,
    QgsProcessingException
)
from qgis.PyQt.QtCore import QVariant
import numpy as np

from ..utils.terrain import raster_to_array, raster_origin, raster_pixel_size
from ..utils.geometry import pixel_to_map


class ErosionAlgorithm(QgsProcessingAlgorithm):

    INPUT_DEM = "INPUT_DEM"
    OUTPUT = "OUTPUT"

    def createInstance(self):
        return ErosionAlgorithm()

    def name(self):
        return "erosion_zones"

    def displayName(self):
        return "Soil Erosion Sensitive Zones"

    def group(self):
        return "Ecosystem"

    def groupId(self):
        return "ecosystem"

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM, "Input DEM"
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT, "Output Erosion Zones", "Shapefile (*.shp)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        if dem is None:
            raise QgsProcessingException("DEM layer not loaded.")

        arr = raster_to_array(dem)

        # Compute slope
        gy, gx = np.gradient(arr)
        slope = np.sqrt(gx ** 2 + gy ** 2)

        # Highest 10% = erosion risk
        threshold = np.percentile(slope, 90)
        erosion_mask = slope >= threshold

        ox, oy = raster_origin(dem)
        pw, ph = raster_pixel_size(dem)

        rows, cols = np.where(erosion_mask)
        feedback.pushInfo(f"Detected {len(rows)} erosion-sensitive pixels.")

        # Convert to points
        pts = [pixel_to_map(ox, oy, pw, ph, r, c) for r, c in zip(rows, cols)]

        if not pts:
            raise QgsProcessingException("No erosion zones detected.")

        geom = QgsGeometry.fromMultiPointXY(pts)

        # ---------------------------
        # Saving to shapefile
        # ---------------------------
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))

        out_path = parameters[self.OUTPUT]

        writer = QgsVectorFileWriter(
            out_path,
            "ESRI Shapefile",
            fields,
            QgsWkbTypes.MultiPoint,
            dem.crs(),
            "UTF-8"
        )

        feat = QgsFeature(fields)
        feat.setAttribute("id", 1)
        feat.setGeometry(geom)

        writer.addFeature(feat)
        del writer

        return {self.OUTPUT: out_path}
