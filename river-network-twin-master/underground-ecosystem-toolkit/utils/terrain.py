from osgeo import gdal
import numpy as np
from qgis.core import QgsRasterLayer

def raster_to_array(raster: QgsRasterLayer):
    """Read raster as numpy 2D array using GDAL (supports any size)."""
    path = raster.source()
    ds = gdal.Open(path)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()
    return arr.astype(float)

def raster_origin(raster: QgsRasterLayer):
    extent = raster.extent()
    return extent.xMinimum(), extent.yMaximum()

def raster_pixel_size(raster: QgsRasterLayer):
    return raster.rasterUnitsPerPixelX(), raster.rasterUnitsPerPixelY()
