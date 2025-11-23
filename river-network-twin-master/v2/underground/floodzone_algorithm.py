from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsGeometry,
    QgsWkbTypes,
    QgsVectorFileWriter,
    QgsProcessingException
)
from qgis.PyQt.QtCore import QVariant


class FloodZoneAlgorithm(QgsProcessingAlgorithm):

    INPUT_LINE = "INPUT_LINE"
    OUTPUT = "OUTPUT"

    def createInstance(self):
        return FloodZoneAlgorithm()

    def name(self):
        return "floodzone_150m"

    def displayName(self):
        return "Flood Protection Zone (150m)"

    def group(self):
        return "Underground Ecosystem"

    def groupId(self):
        return "underground_ecosystem"

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINE,
                "Input River Path (LineString)"
            )
        )

        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                "Output Flood Protection Zone (Polygon)",
                "Shapefile (*.shp)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        layer = self.parameterAsSource(parameters, self.INPUT_LINE, context)
        if layer is None:
            raise QgsProcessingException("Input river layer not found.")

        out_path = self.parameterAsFile(parameters, self.OUTPUT, context)

        feat = next(layer.getFeatures(), None)
        if feat is None:
            raise QgsProcessingException("Input line layer is empty.")

        geom = feat.geometry()

        feedback.pushInfo("Computing 150m buffer...")

        flood_geom = geom.buffer(150, 24)

        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))

        writer = QgsVectorFileWriter(
            out_path,
            "UTF-8",
            fields,
            QgsWkbTypes.Polygon,
            layer.sourceCrs(),
            "ESRI Shapefile"
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise QgsProcessingException("Writer error: " + writer.errorMessage())

        f = QgsFeature()
        f.setFields(fields)
        f.setAttribute("id", 1)
        f.setGeometry(flood_geom)
        writer.addFeature(f)

        del writer

        feedback.pushInfo("Flood protection zone created successfully.")

        return {self.OUTPUT: out_path}

    def createInstance(self):
        return FloodZoneAlgorithm()