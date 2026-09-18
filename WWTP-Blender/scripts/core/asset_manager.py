from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = PROJECT_ROOT / 'assets'

def asset_path(*parts):
    path = ASSET_ROOT.joinpath(*parts)
    if not path.exists():
        raise FileNotFoundError(path)
    return path

def raw_download_path(filename):
    return ASSET_ROOT / 'raw_downloads' / filename
