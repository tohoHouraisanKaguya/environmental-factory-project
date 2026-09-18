import bpy
from mathutils import Vector

def add_box(name, dimensions, location, collection):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for col in list(obj.users_collection): col.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

def add_cylinder(name, radius, depth, location, collection, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object; obj.name = name
    for col in list(obj.users_collection): col.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

def add_pipe(name, start, end, radius, collection):
    a, b = Vector(start), Vector(end); delta = b - a
    obj = add_cylinder(name, radius, delta.length, (a+b)/2, collection)
    obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = Vector((0,0,1)).rotation_difference(delta.normalized())
    return obj
