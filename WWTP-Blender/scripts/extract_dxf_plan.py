"""Extract model-space geometry from the reference DXF into stable JSON."""
from __future__ import annotations
import json
from pathlib import Path
import ezdxf

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references" / "drawings" / "WWTP_Factory_Plan_R2010_2.dxf"
OUTPUT = ROOT / "data" / "plan_extracted.json"
LAYERS = {
    "SITE", "ROAD", "ROAD-CENTER", "GREEN", "ENVELOPE", "STRUCT-OUT", "STRUCT-IN",
    "W-MAIN", "RAS", "IR", "AIR", "SLUDGE", "BYPASS", "FLOW"
}

def point(v):
    return [round(float(v.x), 4), round(float(v.y), 4)]

def extract():
    doc = ezdxf.readfile(SOURCE)
    entities = []
    for entity in doc.modelspace():
        layer = entity.dxf.layer
        kind = entity.dxftype()
        if layer not in LAYERS or kind not in {"LINE", "LWPOLYLINE", "CIRCLE"}:
            continue
        item = {"layer": layer, "type": kind}
        if kind == "LINE":
            item.update(start=point(entity.dxf.start), end=point(entity.dxf.end))
        elif kind == "CIRCLE":
            item.update(center=point(entity.dxf.center), radius=round(float(entity.dxf.radius), 4))
        else:
            item.update(points=[[round(float(v[0]), 4), round(float(v[1]), 4)] for v in entity.get_points()], closed=bool(entity.closed))
        entities.append(item)
    payload = {
        "source": SOURCE.name,
        "dxf_version": doc.dxfversion,
        "insunits_code": int(doc.header.get("$INSUNITS", 0)),
        "units": "m",
        "site_bounds": [0.0, 0.0, 400.0, 300.0],
        "provisional_verticals": {"tank_wall_height": 4.5, "building_height": 8.0, "pipe_elevation": 1.2},
        "entities": entities,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload

if __name__ == "__main__":
    result = extract()
    print(f"Wrote {len(result['entities'])} entities to {OUTPUT}")
