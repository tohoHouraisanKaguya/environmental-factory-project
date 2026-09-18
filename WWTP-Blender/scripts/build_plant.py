"""Formal plant build entry point; intentionally blocked pending approved design inputs."""
from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_from_plan import build as build_from_plan

def build():
    data = json.loads((ROOT.parent / 'data' / 'plant.json').read_text(encoding='utf-8'))
    if data['status'] != 'approved_for_generation':
        raise RuntimeError('Formal plant generation is blocked until approved drawings and parameters are supplied.')
    return build_from_plan(render=True)

if __name__ == '__main__': build()
