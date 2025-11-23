from qgis.core import QgsPointXY

def pixel_to_map(origin_x, origin_y, pixel_width, pixel_height, row, col):
    """Convert raster pixel index -> map coordinate"""
    x = origin_x + col * pixel_width
    y = origin_y - row * abs(pixel_height)
    return QgsPointXY(x, y)