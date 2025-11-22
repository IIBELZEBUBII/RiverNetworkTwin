from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from qgis.PyQt.QtWidgets import QMessageBox

from src.least_cost_path.least_cost_path import coord_to_pixel


def load_vector_layer(layer_path: Path, name: str) -> QgsVectorLayer:
    layer = QgsVectorLayer(str(layer_path), name, "ogr")
    if not layer.isValid():
        QMessageBox.warning(
            None,
            "Ошибка слоя",
            f"Не удалось загрузить слой {name} по пути {layer_path}",
        )
        raise RuntimeError(f"Layer {name} is invalid: {layer_path}")
    QgsProject.instance().addMapLayer(layer)
    return layer


def features_to_nodes(
    layer: QgsVectorLayer,
    target_crs: QgsCoordinateReferenceSystem,
    geotransform: Tuple[float, ...],
    rows: int,
    cols: int,
) -> List[int]:
    transform = QgsCoordinateTransform(layer.crs(), target_crs, QgsProject.instance())
    nodes: List[int] = []
    for feature in layer.getFeatures():
        pt = _geometry_to_point(feature)
        if pt is None:
            continue
        raster_point = transform.transform(pt)
        i, j = coord_to_pixel(raster_point.x(), raster_point.y(), geotransform)
        if not (0 <= i < rows and 0 <= j < cols):
            continue
        nodes.append(i * cols + j)
    if not nodes:
        raise RuntimeError(
            f"Слой {layer.name()} не содержит валидных точек в пределах растрового покрытия."
        )
    return nodes


def _geometry_to_point(feature: QgsFeature) -> QgsPointXY | None:
    geom: QgsGeometry = feature.geometry()
    if geom.isEmpty():
        return None
    if geom.isMultipart():
        multipoint = geom.asMultiPoint()
        if multipoint:
            return QgsPointXY(multipoint[0])
        parts: Iterable[QgsGeometry] = geom.asGeometryCollection()
        for part in parts:
            pt = part.asPoint()
            if pt:
                return QgsPointXY(pt)
        return None
    return QgsPointXY(geom.asPoint())

