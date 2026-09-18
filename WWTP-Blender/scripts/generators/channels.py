def build(spec, collection, material=None):
    from rectangular_tank import build as rectangular_build
    return rectangular_build(spec, collection, material)
