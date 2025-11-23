from dataclasses import dataclass
from pathlib import Path


@dataclass
class RusleInputs:
    rainfall_path: Path
    soil_erodibility_path: Path
    slope_length_path: Path
    cover_management_path: Path
    support_practice_path: Path
    crs_auth_id: str = "EPSG:3857"

