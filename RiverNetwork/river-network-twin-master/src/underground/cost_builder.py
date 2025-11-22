from __future__ import annotations

from pathlib import Path

import numpy as np
from osgeo import gdal

from .config import UndergroundCostWeights, UndergroundInputs


def build_cost_raster(
    inputs: UndergroundInputs,
    weights: UndergroundCostWeights,
    output_path: Path,
) -> Path:
    dem = gdal.Open(str(inputs.dem_path))
    gw = gdal.Open(str(inputs.groundwater_path))
    permeability = gdal.Open(str(inputs.permeability_path))
    karst = gdal.Open(str(inputs.karst_path))

    dem_arr = dem.GetRasterBand(1).ReadAsArray().astype("float32")
    gw_arr = gw.GetRasterBand(1).ReadAsArray().astype("float32")
    perm_arr = permeability.GetRasterBand(1).ReadAsArray().astype("float32")
    karst_arr = karst.GetRasterBand(1).ReadAsArray().astype("float32")

    slope_x, slope_y = np.gradient(gw_arr)
    slope = np.abs(slope_x) + np.abs(slope_y)
    slope = normalize_array(slope)

    perm_norm = 1.0 - normalize_array(perm_arr)
    karst_norm = 1.0 - normalize_array(karst_arr)

    depth = dem_arr - gw_arr
    depth_penalty = normalize_array(np.clip(depth, 0, None))

    cost = (
        weights.slope * slope
        + weights.permeability * perm_norm
        + weights.karst * karst_norm
        + weights.depth * depth_penalty
    ).astype("float32")

    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(
        str(output_path),
        dem.RasterXSize,
        dem.RasterYSize,
        1,
        gdal.GDT_Float32,
    )
    out_ds.SetGeoTransform(dem.GetGeoTransform())
    out_ds.SetProjection(dem.GetProjection())
    out_ds.GetRasterBand(1).WriteArray(cost)
    out_ds.FlushCache()
    out_ds = None
    return output_path


def normalize_array(arr: np.ndarray) -> np.ndarray:
    arr_min = np.nanmin(arr)
    arr_max = np.nanmax(arr)
    if arr_max - arr_min == 0:
        return np.zeros_like(arr, dtype="float32")
    return ((arr - arr_min) / (arr_max - arr_min)).astype("float32")

