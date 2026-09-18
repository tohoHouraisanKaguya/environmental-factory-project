"""Parameter-driven rectangular tank geometry."""
from core.geometry import add_box

def build(spec, collection, material=None):
    length, width, depth, wall = (spec[k] for k in ('length','width','depth','wall_thickness'))
    x, y, z = spec.get('location', (0,0,0))
    parts = []
    for i, (dims, loc) in enumerate(((length, wall, depth), (length, wall, depth), (wall, width, depth), (wall, width, depth))):
        dx = 0 if i < 2 else ((-length + wall)/2 if i == 2 else (length-wall)/2)
        dy = ((-width+wall)/2 if i == 0 else (width-wall)/2) if i < 2 else 0
        obj=add_box(f"TANK_{spec['id']}_{i+1:02d}",dims,(x+dx,y+dy,z+depth/2),collection)
        if material: obj.data.materials.append(material)
        parts.append(obj)
    return parts
