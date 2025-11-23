from __future__ import annotations

from pathlib import Path

import processing
from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from qgis.core import QgsProject

from src.progress_manager import ProgressManager

from .analysis import build_weathering_mask, compute_weathering_index
from .config import WeatheringInputs


def _prompt_raster(title: str) -> Path | None:
    path, _ = QFileDialog.getOpenFileName(None, title, "", "GeoTIFF (*.tif)")
    return Path(path) if path else None


def _prompt_vector(title: str) -> Path | None:
    path, _ = QFileDialog.getOpenFileName(None, title, "", "Vector (*.gpkg *.shp)")
    return Path(path) if path else None


def weathering_zone_analysis(project_folder: Path) -> None:
    watershed = _prompt_vector("Выберите слой водоразделов")
    slope = _prompt_raster("Выберите растр уклонов")
    moisture = _prompt_raster("Выберите растр влажности / увлажнения")
    lithology = _prompt_raster("Выберите растр литологии (индекс выветривания)")
    temperature = _prompt_raster("Выберите растр температурной амплитуды")
    if not all([watershed, slope, moisture, lithology, temperature]):
        QMessageBox.warning(None, "Недостаточно данных", "Необходимы все входные слои.")
        return

    percentile, ok = QInputDialog.getDouble(
        None,
        "Пороговый процентиль",
        "Процент пикселей с наибольшим индексом выветривания:",
        value=85.0,
        min=50.0,
        max=99.9,
        decimals=1,
    )
    if not ok:
        return

    inputs = WeatheringInputs(
        watershed_path=watershed,
        slope_path=slope,
        moisture_path=moisture,
        lithology_path=lithology,
        temperature_path=temperature,
    )

    progress = ProgressManager("Зоны выветривания", "Расчёт индекса")
    progress.init_progress(100)
    try:
        if not progress.update(20, "Расчёт индекса"):
            return
        index_raster = compute_weathering_index(inputs, project_folder / "weathering_index.tif")

        if not progress.update(60, "Создание маски"):
            return
        mask = build_weathering_mask(index_raster, percentile, project_folder / "weathering_mask.tif")

        if not progress.update(75, "Полигонализация"):
            return
        polygons = processing.run(
            "gdal:polygonize",
            {
                "INPUT": str(mask),
                "BAND": 1,
                "FIELD": "weather",
                "OUTPUT": "TEMPORARY_OUTPUT",
            },
        )["OUTPUT"]

        if not progress.update(90, "Пересечение с водоразделами"):
            return
        intersection = processing.run(
            "native:intersection",
            {
                "INPUT": str(watershed),
                "OVERLAY": polygons,
                "INPUT_FIELDS": [],
                "OVERLAY_FIELDS": [],
                "OUTPUT": str(project_folder / "weathering_zones.gpkg"),
            },
        )["OUTPUT"]
        intersection.setName("Weathering zones")
        QgsProject.instance().addMapLayer(intersection)
        progress.update(100, "Готово!")
    finally:
        progress.finish()

