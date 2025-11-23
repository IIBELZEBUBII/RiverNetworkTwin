from __future__ import annotations

from pathlib import Path

import processing
from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from qgis.core import QgsProject

from src.progress_manager import ProgressManager

from .analysis import compute_rusle, create_risk_mask
from .config import RusleInputs


def _prompt_raster(title: str) -> Path | None:
    path, _ = QFileDialog.getOpenFileName(None, title, "","GeoTIFF (*.tif)")
    return Path(path) if path else None


def soil_erosion_analysis(project_folder: Path) -> None:
    rainfall = _prompt_raster("Выберите растр осадков (R)")
    soil = _prompt_raster("Выберите растр размываемости почв (K)")
    slope = _prompt_raster("Выберите растр LS-фактора")
    cover = _prompt_raster("Выберите растр покрова (C)")
    support = _prompt_raster("Выберите растр защитных практик (P)")
    if not all([rainfall, soil, slope, cover, support]):
        QMessageBox.warning(None, "Недостаточно данных", "Все пять растров R,K,LS,C,P обязательны.")
        return

    threshold, ok = QInputDialog.getDouble(
        None,
        "Порог риска",
        "Минимальная потеря почвы (т/га/год) для высокого риска:",
        value=10.0,
        min=0.1,
        max=1000.0,
        decimals=2,
    )
    if not ok:
        return

    inputs = RusleInputs(
        rainfall_path=rainfall,
        soil_erodibility_path=soil,
        slope_length_path=slope,
        cover_management_path=cover,
        support_practice_path=support,
    )

    progress = ProgressManager("Риск эрозии", "Подготовка...")
    progress.init_progress(100)
    try:
        if not progress.update(10, "Расчёт RUSLE"):
            return
        erosion_raster = compute_rusle(inputs, project_folder / "soil_loss.tif")

        if not progress.update(50, "Формирование маски риска"):
            return
        mask = create_risk_mask(erosion_raster, threshold, project_folder / "soil_risk_mask.tif")

        if not progress.update(80, "Полигонализация"):
            return
        polygons = processing.run(
            "gdal:polygonize",
            {
                "INPUT": str(mask),
                "BAND": 1,
                "FIELD": "risk",
                "OUTPUT": str(project_folder / "soil_erosion_zones.gpkg"),
            },
        )["OUTPUT"]
        polygons.setName("Soil erosion zones")
        QgsProject.instance().addMapLayer(polygons)
        progress.update(100, "Готово!")
    finally:
        progress.finish()

