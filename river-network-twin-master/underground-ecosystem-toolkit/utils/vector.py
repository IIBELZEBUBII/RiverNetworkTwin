from qgis.core import (
    QgsFields, QgsField, QgsFeature,
    QgsWkbTypes, QgsVectorFileWriter
)
from qgis.PyQt.QtCore import QVariant

def save_polygon(path, crs, geometry):
    fields = QgsFields()
    fields.append(QgsField("id", QVariant.Int))

    writer = QgsVectorFileWriter.create(
        path,
        fields,
        QgsWkbTypes.Polygon,
        crs,
        QgsVectorFileWriter.SaveVectorOptions()
    )

    feat = QgsFeature()
    feat.setFields(fields)
    feat.setAttribute("id", 1)
    feat.setGeometry(geometry)

    writer.addFeature(feat)
    del writer