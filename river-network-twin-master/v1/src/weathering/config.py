from dataclasses import dataclass
from pathlib import Path


@dataclass
class WeatheringInputs:
    watershed_path: Path
    slope_path: Path
    moisture_path: Path
    lithology_path: Path
    temperature_path: Path
    crs_auth_id: str = "EPSG:3857"

