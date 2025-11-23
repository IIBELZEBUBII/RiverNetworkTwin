from __future__ import annotations

from pathlib import Path

from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from src.progress_manager import ProgressManager

from .config import UndergroundCostWeights, UndergroundInputs
from .cost_builder import build_cost_raster
from .datasource import load_vector_layer
from .network import run_network_analysis
from .polygonizer import polygonize_paths


def prompt_file_path(caption: str, filter_mask: str) -> Path | None:
    path, _ = QFileDialog.getOpenFileName(None, caption, "", filter_mask)
    return Path(path) if path else None


def underground_river_analysis(project_folder: Path) -> None:
    dem = prompt_file_path("Выберите DEM", "GeoTIFF (*.tif)")
    gw = prompt_file_path("Выберите поверхность грунтовых вод", "GeoTIFF (*.tif)")
    perm = prompt_file_path("Выберите слой проницаемости", "GeoTIFF (*.tif)")
    karst = prompt_file_path("Выберите слой карстового индекса", "GeoTIFF (*.tif)")
    sources = prompt_file_path("Выберите источник подземных вод", "Vector (*.gpkg *.shp)")
    sinks = prompt_file_path("Выберите точку выхода подземной реки", "Vector (*.gpkg *.shp)")

    if not all([dem, gw, perm, karst, sources, sinks]):
        QMessageBox.warning(None, "Недостаточно данных", "Все файлы должны быть выбраны.")
        return

    slope_weight, ok = QInputDialog.getDouble(
        None, "Вес уклона", "Введите вес уклона (0-1)", value=0.4, min=0.0, max=1.0
    )
    if not ok:
        return
    permeability_weight, ok = QInputDialog.getDouble(
        None, "Вес проницаемости", "Введите вес проницаемости (0-1)", value=0.25, min=0.0, max=1.0
    )
    if not ok:
        return

    karst_weight, ok = QInputDialog.getDouble(
        None, "Вес карстового индекса", "Введите вес карста (0-1)", value=0.2, min=0.0, max=1.0
    )
    if not ok:
        return
    depth_weight = max(0.0, 1.0 - slope_weight - permeability_weight - karst_weight)

    inputs = UndergroundInputs(
        dem_path=dem,
        groundwater_path=gw,
        permeability_path=perm,
        karst_path=karst,
        source_points_path=sources,
        outlet_points_path=sinks,
    )
    weights = UndergroundCostWeights(
        slope=slope_weight,
        permeability=permeability_weight,
        karst=karst_weight,
        depth=depth_weight,
    )

    progress = ProgressManager("Подземные водоразделы", "Подготовка входных данных...")
    progress.init_progress(100)
    try:
        if not progress.update(5, "Создание слоя стоимости"):
            return
        cost_raster = build_cost_raster(
            inputs, weights, project_folder / "underground_cost.tif"
        )

        if not progress.update(20, "Загрузка точек"):
            return
        sources_layer = load_vector_layer(
            inputs.source_points_path, "Underground sources"
        )
        sinks_layer = load_vector_layer(inputs.outlet_points_path, "Underground sinks")

        if not progress.update(30, "Расчёт путей"):
            return
        path_layer = run_network_analysis(
            cost_raster,
            sources_layer,
            sinks_layer,
            project_folder / "underground_paths.gpkg",
            inputs.crs_auth_id,
            progress,
        )

        if not progress.update(90, "Построение полигонов"):
            return
        polygonize_paths(path_layer, project_folder / "underground_basins.gpkg")
        progress.update(100, "Готово!")
    finally:
        progress.finish()

