from __future__ import annotations

from pathlib import Path

import numpy as np
from osgeo import gdal

from .config import RusleInputs


def compute_rusle(inputs: RusleInputs, output_path: Path) -> Path:
    rainfall = gdal.Open(str(inputs.rainfall_path))
    soil = gdal.Open(str(inputs.soil_erodibility_path))
    slope = gdal.Open(str(inputs.slope_length_path))
    cover = gdal.Open(str(inputs.cover_management_path))
    support = gdal.Open(str(inputs.support_practice_path))

    arrays = [
        rainfall.GetRasterBand(1).ReadAsArray().astype("float32"),
        soil.GetRasterBand(1).ReadAsArray().astype("float32"),
        slope.GetRasterBand(1).ReadAsArray().astype("float32"),
        cover.GetRasterBand(1).ReadAsArray().astype("float32"),
        support.GetRasterBand(1).ReadAsArray().astype("float32"),
    ]

    result = np.ones_like(arrays[0], dtype="float32")
    for arr in arrays:
        result *= np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(
        str(output_path),
        rainfall.RasterXSize,
        rainfall.RasterYSize,
        1,
        gdal.GDT_Float32,
    )
    out_ds.SetGeoTransform(rainfall.GetGeoTransform())
    out_ds.SetProjection(rainfall.GetProjection())
    out_ds.GetRasterBand(1).WriteArray(result)
    out_ds.GetRasterBand(1).SetNoDataValue(-9999)
    out_ds.FlushCache()
    out_ds = None
    return output_path


def create_risk_mask(
    erosion_raster: Path,
    threshold: float,
    mask_output: Path,
) -> Path:
    dataset = gdal.Open(str(erosion_raster))
    data = dataset.GetRasterBand(1).ReadAsArray().astype("float32")
    mask = (data >= threshold).astype("uint8")
    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(
        str(mask_output),
        dataset.RasterXSize,
        dataset.RasterYSize,
        1,
        gdal.GDT_Byte,
    )
    out_ds.SetGeoTransform(dataset.GetGeoTransform())
    out_ds.SetProjection(dataset.GetProjection())
    out_ds.GetRasterBand(1).WriteArray(mask)
    out_ds.GetRasterBand(1).SetNoDataValue(0)
    out_ds.FlushCache()
    out_ds = None
    return mask_output

