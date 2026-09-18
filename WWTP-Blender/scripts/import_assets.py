"""Asset import placeholder: raw assets remain immutable; optimized copies are separate."""
from pathlib import Path
from core.asset_manager import asset_path

def import_asset(relative_path):
    path = asset_path(*Path(relative_path).parts)
    raise NotImplementedError(f"Validate units, normals, licences, origins and polycount before importing {path}")
