"""Disposable MCP/Blender verification scene. Creates, renders, then removes TEST."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))

import bpy
from math import radians
from core.scene_utils import configure_metric_units, clean_orphans
from core.collections import ensure_tree, remove_collection
from core.materials import ensure_principled, assign
from core.geometry import add_box, add_pipe
from generators.equipment_proxy import build_valve_proxy

def ensure_test_collection():
    remove_collection('TEST')
    col = bpy.data.collections.new('TEST')
    bpy.context.scene.collection.children.link(col)
    return col

def configure_camera(target):
    bpy.ops.object.camera_add(location=(18, -20, 16))
    cam = bpy.context.object; cam.name = 'TEST_Camera_01'
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    return cam

def run():
    configure_metric_units()
    ensure_tree()
    test = ensure_test_collection()
    concrete = ensure_principled('MAT_Test_Concrete', (0.36, 0.38, 0.39), roughness=0.82)
    metal = ensure_principled('MAT_Test_Metal', (0.12, 0.16, 0.18), metallic=0.88, roughness=0.28)

    # 10 m x 6 m x 1 m test concrete tank base.
    tank = add_box('TEST_ConcreteTank_01', (10.0, 6.0, 1.0), (0, 0, 0.5), test)
    assign(tank, concrete)
    pipe = add_pipe('TEST_Pipe_01', (-6, 0, 1.5), (6, 0, 1.5), 0.25, test)
    assign(pipe, metal)
    valve = build_valve_proxy({'id':'Test','radius':0.45,'length':0.65,'location':(0,0,1.5)}, test, metal)
    valve.rotation_euler[1] = radians(90)

    camera = configure_camera(tank.location)
    for obj in (camera,):
        for col in list(obj.users_collection): col.objects.unlink(obj)
        test.objects.link(obj)
    scene = bpy.context.scene
    # Blender 5.2 exposes the Eevee renderer as BLENDER_EEVEE.
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 960; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(PROJECT / 'renders' / 'previews' / 'test_scene_isometric.png')
    scene.render.film_transparent = False
    scene.world.color = (0.045, 0.055, 0.07)
    bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT / 'blender' / 'plant.blend'))
    bpy.ops.render.render(write_still=True)
    if tuple(round(v, 3) for v in tank.dimensions) != (10.0, 6.0, 1.0):
        raise RuntimeError(f'Unit check failed: {tuple(tank.dimensions)}')
    remove_collection('TEST')
    clean_orphans()
    bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT / 'blender' / 'plant.blend'))
    return {'render': scene.render.filepath, 'saved': str(PROJECT / 'blender' / 'plant.blend')}

if __name__ == '__main__':
    print(run())
