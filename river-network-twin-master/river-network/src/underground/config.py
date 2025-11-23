from dataclasses import dataclass
from pathlib import Path


@dataclass
class UndergroundCostWeights:
    """Weights for building underground cost surfaces."""

    slope: float = 0.4
    permeability: float = 0.25
    karst: float = 0.2
    depth: float = 0.15


@dataclass
class UndergroundInputs:
    """Container with file paths needed for underground analysis."""

    dem_path: Path
    groundwater_path: Path
    permeability_path: Path
    karst_path: Path
    source_points_path: Path | None = None
    outlet_points_path: Path | None = None
    crs_auth_id: str = "EPSG:3857"

