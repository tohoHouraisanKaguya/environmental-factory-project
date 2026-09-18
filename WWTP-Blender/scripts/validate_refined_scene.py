"""Read-only validation for the generated wastewater plant scene."""
from pathlib import Path
import bpy

scene = bpy.context.scene
names = [obj.name for obj in bpy.data.objects]
grids = [obj for obj in bpy.data.objects if obj.name.startswith('AERATOR_GRID_') and not obj.name.endswith('_Disc_Source')]
instances = [obj for obj in bpy.data.objects if obj.instance_type == 'COLLECTION']
missing_images = []
for image in bpy.data.images:
    if image.source == 'FILE' and image.filepath:
        path = Path(bpy.path.abspath(image.filepath))
        if not path.exists():
            missing_images.append(str(path))

report = {
    'unit_system': scene.unit_settings.system,
    'length_unit': scene.unit_settings.length_unit,
    'scale_length': scene.unit_settings.scale_length,
    'object_count': len(bpy.data.objects),
    'duplicate_object_names': len(names) - len(set(names)),
    'collection_instances': len(instances),
    'street_lights': len([o for o in instances if o.name.startswith('LIGHT_Street_')]),
    'valves': len([o for o in instances if o.name.startswith('VALVE_Generic_')]),
    'blower_proxies': len([o for o in instances if o.name.startswith('BLOWER_VisualProxy_')]),
    'pump_proxies': len([o for o in instances if o.name.startswith('PUMP_RAS_VisualProxy_')]),
    'chemical_tanks': len([o for o in bpy.data.objects if o.name.startswith('TANK_Chemical_20m3_') and not o.name.endswith('_Source')]),
    'aerator_grids': len(grids),
    'aerator_instances_declared': sum(int(o.get('instance_count', 0)) for o in grids),
    'geometry_nodes_grids': sum(any(m.type == 'NODES' for m in o.modifiers) for o in grids),
    'missing_images': missing_images,
    'pbr_materials': [name for name in ('MAT_Concrete','MAT_Asphalt','MAT_Grass','MAT_Metal') if bpy.data.materials.get(name)],
}
print('VALIDATION', report)
assert report['unit_system'] == 'METRIC' and report['length_unit'] == 'METERS' and report['scale_length'] == 1.0
assert report['duplicate_object_names'] == 0
assert report['aerator_instances_declared'] == 6000 and report['geometry_nodes_grids'] == 4
assert not missing_images
