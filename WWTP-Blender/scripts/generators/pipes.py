from core.geometry import add_pipe

def build_route(spec, collection, material=None):
    obj=add_pipe(f"PIPE_{spec['id']}_01", spec['start'], spec['end'], spec['radius'], collection)
    if material: obj.data.materials.append(material)
    return obj
