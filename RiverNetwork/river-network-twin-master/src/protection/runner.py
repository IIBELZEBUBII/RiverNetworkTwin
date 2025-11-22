from __future__ import annotations

from pathlib import Path

import processing
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes
from qgis.PyQt.QtWidgets import QInputDialog, QMessageBox

from src.progress_manager import ProgressManager


def _ask_distance(title: str, default: float) -> float | None:
    value, ok = QInputDialog.getDouble(None, title, "Значение, м:", default, 0, 50000, 2)
    return value if ok else None


def protection_zone_analysis(project_folder: Path) -> None:
    project = QgsProject.instance()
    polygon_layers = [
        layer
        for layer in project.mapLayers().values()
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry
    ]
    if not polygon_layers:
        QMessageBox.warning(None, "Нет полигонов", "Добавьте слой водоразделов.")
        return
    poly_names = [layer.name() for layer in polygon_layers]
    basin_name, ok = QInputDialog.getItem(
        None, "Слой водоразделов", "Выберите слой:", poly_names, 0, False
    )
    if not ok:
        return
    basin_layer = next(layer for layer in polygon_layers if layer.name() == basin_name)

    line_layers = [
        layer
        for layer in project.mapLayers().values()
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.LineGeometry
    ]
    if not line_layers:
        QMessageBox.warning(None, "Нет линий", "Добавьте слой рек.")
        return
    line_names = [layer.name() for layer in line_layers]
    river_name, ok = QInputDialog.getItem(
        None, "Слой рек", "Выберите слой рек:", line_names, 0, False
    )
    if not ok:
        return
    river_layer = next(layer for layer in line_layers if layer.name() == river_name)

    surface_distance = _ask_distance("Поверхностный буфер (м)", 200.0)
    if surface_distance is None:
        return
    subsurface_distance = _ask_distance("Подземный буфер (м)", 500.0)
    if subsurface_distance is None:
        return

    progress = ProgressManager("Защитные зоны", "Расчёт буферов")
    progress.init_progress(100)
    try:
        surface = processing.run(
            "native:buffer",
            {
                "INPUT": river_layer,
                "DISTANCE": surface_distance,
                "SEGMENTS": 24,
                "END_CAP_STYLE": 0,
                "DISSOLVE": True,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )["OUTPUT"]
        progress.update(30, "Буфер рек")

        subsurface = processing.run(
            "native:buffer",
            {
                "INPUT": basin_layer,
                "DISTANCE": subsurface_distance,
                "SEGMENTS": 16,
                "END_CAP_STYLE": 0,
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )["OUTPUT"]
        progress.update(60, "Буфер подземных зон")

        merged = processing.run(
            "native:mergevectorlayers",
            {"LAYERS": [surface, subsurface], "CRS": basin_layer.crs(), "OUTPUT": "TEMPORARY_OUTPUT"},
        )["OUTPUT"]
        classified = processing.run(
            "native:fieldcalculator",
            {
                "INPUT": merged,
                "FIELD_NAME": "zone",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 64,
                "FORMULA": "CASE WHEN $id=0 THEN 'surface' ELSE 'subsurface' END",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )["OUTPUT"]
        dissolved = processing.run(
            "native:dissolve",
            {"INPUT": classified, "FIELD": ["zone"], "OUTPUT": str(project_folder / "protection_zones.gpkg")},
        )["OUTPUT"]
        dissolved.setName("Protection zones")
        QgsProject.instance().addMapLayer(dissolved)
        progress.update(100, "Готово")
    finally:
        progress.finish()

