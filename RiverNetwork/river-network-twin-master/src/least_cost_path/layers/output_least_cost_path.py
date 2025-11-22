from pathlib import Path
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsField,
    QgsFields,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant


def build_output_least_cost_path(
    point_layer_path: Path,
    layer_name: str = "Output least cost path",
    crs_auth_id: str = "EPSG:3857",
) -> QgsVectorLayer:
    crs = QgsCoordinateReferenceSystem(crs_auth_id)

    # Определяем поля слоя
    fields = QgsFields()
    fields.append(QgsField("start_id", QVariant.Int))
    fields.append(QgsField("end_id", QVariant.Int))

    # Готовим параметры сохранения (SaveVectorOptions)
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.fileEncoding = "UTF-8"
    options.layerName = layer_name

    # Получаем контекст преобразований из проекта
    transform_context = QgsProject.instance().transformContext()

    # Создаем GeoPackage-слой
    QgsVectorFileWriter.create(
        str(point_layer_path),
        fields,
        QgsWkbTypes.LineString,
        crs,
        transform_context,
        options,
    )

    # Открываем и добавляем в проект
    uri = f"{str(point_layer_path)}|layername={layer_name}"
    return QgsVectorLayer(uri, layer_name, "ogr")
