from core.geometry import add_cylinder

def build(spec, collection, material=None):
    obj=add_cylinder(f"CLARIFIER_{spec['id']}_01", spec['diameter']/2, spec['wall_height'], spec.get('location',(0,0,0)), collection)
    if material: obj.data.materials.append(material)
    return obj
