from __future__ import annotations

from pathlib import Path

import numpy as np
from osgeo import gdal

from .config import WeatheringInputs


def compute_weathering_index(inputs: WeatheringInputs, output_path: Path) -> Path:
    slope = gdal.Open(str(inputs.slope_path))
    moisture = gdal.Open(str(inputs.moisture_path))
    lithology = gdal.Open(str(inputs.lithology_path))
    temperature = gdal.Open(str(inputs.temperature_path))

    slope_arr = normalize_array(slope.GetRasterBand(1).ReadAsArray().astype("float32"))
    moisture_arr = normalize_array(
        moisture.GetRasterBand(1).ReadAsArray().astype("float32")
    )
    lith_arr = normalize_array(
        lithology.GetRasterBand(1).ReadAsArray().astype("float32")
    )
    temp_arr = normalize_array(
        temperature.GetRasterBand(1).ReadAsArray().astype("float32")
    )

    # Weathering more intense on gentle slopes (low slope), high moisture, high temp amplitude
    index = (1.0 - slope_arr) * moisture_arr * temp_arr * lith_arr
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(
        str(output_path),
        slope.RasterXSize,
        slope.RasterYSize,
        1,
        gdal.GDT_Float32,
    )
    out_ds.SetGeoTransform(slope.GetGeoTransform())
    out_ds.SetProjection(slope.GetProjection())
    out_ds.GetRasterBand(1).WriteArray(index.astype("float32"))
    out_ds.GetRasterBand(1).SetNoDataValue(-9999)
    out_ds.FlushCache()
    out_ds = None
    return output_path


def build_weathering_mask(
    index_raster: Path, percentile: float, output_path: Path
) -> Path:
    ds = gdal.Open(str(index_raster))
    data = ds.GetRasterBand(1).ReadAsArray().astype("float32")
    valid = data[np.isfinite(data)]
    if valid.size == 0:
        threshold = 0.0
    else:
        threshold = np.percentile(valid, percentile)
    mask = (data >= threshold).astype("uint8")
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(
        str(output_path),
        ds.RasterXSize,
        ds.RasterYSize,
        1,
        gdal.GDT_Byte,
    )
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())
    out_ds.GetRasterBand(1).WriteArray(mask)
    out_ds.GetRasterBand(1).SetNoDataValue(0)
    out_ds.FlushCache()
    out_ds = None
    return output_path


def normalize_array(arr: np.ndarray) -> np.ndarray:
    arr_min = np.nanmin(arr)
    arr_max = np.nanmax(arr)
    if arr_max - arr_min == 0:
        return np.zeros_like(arr, dtype="float32")
    return ((arr - arr_min) / (arr_max - arr_min)).astype("float32")

