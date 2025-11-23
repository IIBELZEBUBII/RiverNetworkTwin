from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import networkit as nk
from osgeo import gdal
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)
from src.least_cost_path.least_cost_path import pixel_to_coord
from src.least_cost_path.layers.output_least_cost_path import build_output_least_cost_path
from src.underground.datasource import features_to_nodes


def build_cost_graph(raster_path: Path) -> Tuple[nk.Graph, Tuple[float, ...], int, int]:
    dataset = gdal.Open(str(raster_path))
    arr = dataset.GetRasterBand(1).ReadAsArray().astype("float32")
    rows, cols = arr.shape
    graph = nk.Graph(rows * cols, weighted=True, directed=False)
    neighbors = [
        (1, 0, 1.0),
        (0, 1, 1.0),
        (1, 1, 2**0.5),
        (1, -1, 2**0.5),
    ]

    def node_id(i: int, j: int) -> int:
        return i * cols + j

    for i in range(rows):
        for j in range(cols):
            for di, dj, factor in neighbors:
                ni, nj = i + di, j + dj
                if 0 <= ni < rows and 0 <= nj < cols:
                    weight = factor * (arr[i, j] + arr[ni, nj]) / 2
                    graph.addEdge(node_id(i, j), node_id(ni, nj), float(weight))

    return graph, dataset.GetGeoTransform(), rows, cols


def add_paths_to_layer(
    layer,
    node_path: Sequence[int],
    cols: int,
    geotransform: Sequence[float],
    start_id: int,
    end_id: int,
):
    geometry = [
        QgsPointXY(*pixel_to_coord(idx // cols, idx % cols, geotransform))
        for idx in node_path
    ]
    feature = QgsFeature(layer.fields())
    feature.setAttributes([start_id, end_id])
    feature.setGeometry(QgsGeometry.fromPolylineXY(geometry))
    layer.dataProvider().addFeature(feature)


def _update(progress, value, message):
    if progress is None:
        return True
    return progress.update(value, message)


def run_network_analysis(
    cost_raster: Path,
    sources_layer: QgsVectorLayer,
    sinks_layer: QgsVectorLayer,
    output_path: Path,
    crs_auth_id: str,
    progress=None,
) -> QgsVectorLayer:
    graph, geotransform, rows, cols = build_cost_graph(cost_raster)

    dataset = gdal.Open(str(cost_raster))
    raster_crs = QgsCoordinateReferenceSystem(dataset.GetProjection())
    source_nodes = features_to_nodes(sources_layer, raster_crs, geotransform, rows, cols)
    sink_nodes = features_to_nodes(sinks_layer, raster_crs, geotransform, rows, cols)

    path_layer = build_output_least_cost_path(
        output_path,
        layer_name="Underground least cost path",
        crs_auth_id=crs_auth_id,
    )

    dijkstras: Dict[int, nk.distance.Dijkstra] = {}
    total = len(source_nodes) * len(sink_nodes)
    processed = 0
    for src_idx, src_node in enumerate(source_nodes):
        if progress and progress.was_canceled():
            break
        _update(
            progress,
            40 + int(40 * src_idx / max(1, len(source_nodes))),
            f"Пути от источника {src_idx + 1}/{len(source_nodes)}",
        )
        if src_node not in dijkstras:
            dijk = nk.distance.Dijkstra(graph, src_node, storePaths=True)
            dijk.run()
            dijkstras[src_node] = dijk
        else:
            dijk = dijkstras[src_node]
        for sink_idx, sink_node in enumerate(sink_nodes):
            processed += 1
            if processed % 10 == 0:
                _update(
                    progress,
                    40 + int(40 * processed / max(1, total)),
                    f"Комбинации {processed}/{total}",
                )
            path = dijk.getPath(sink_node)
            if len(path) < 2:
                continue
            add_paths_to_layer(
                path_layer,
                path,
                cols,
                geotransform,
                start_id=src_idx + 1,
                end_id=sink_idx + 1,
            )

    path_layer.updateExtents()
    QgsProject.instance().addMapLayer(path_layer)
    return path_layer
