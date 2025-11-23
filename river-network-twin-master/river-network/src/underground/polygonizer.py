from __future__ import annotations

from pathlib import Path

import processing
from qgis.core import QgsProject, QgsVectorLayer


def polygonize_paths(path_layer: QgsVectorLayer, output_path: Path) -> QgsVectorLayer:
    dissolve = processing.run(
        "native:dissolve",
        {"INPUT": path_layer, "OUTPUT": "TEMPORARY_OUTPUT"},
    )["OUTPUT"]
    polygons = processing.run(
        "native:polygonize",
        {"INPUT": dissolve, "OUTPUT": str(output_path)},
    )["OUTPUT"]
    QgsProject.instance().addMapLayer(polygons)
    polygons.setName("Underground basins")
    return polygons

