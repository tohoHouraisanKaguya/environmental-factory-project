def build(spec, collection, material=None):
    from core.geometry import add_box
    obj=add_box(f"ROAD_{spec['id']}_01", spec['dimensions'], spec['location'], collection)
    if material: obj.data.materials.append(material)
    return obj
