from core.geometry import add_cylinder

def build_valve_proxy(spec, collection, material=None):
    obj=add_cylinder(f"VALVE_{spec['id']}_01", spec.get('radius',0.35), spec.get('length',0.5), spec.get('location',(0,0,0)), collection, rotation=(0,1.5708,0))
    if material: obj.data.materials.append(material)
    return obj
