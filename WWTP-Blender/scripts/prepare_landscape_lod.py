"""Build cached, normalized CC0 asset LODs without changing original downloads."""
import bpy, json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
report=[]
for aid,budget,category,folder in [('jacaranda_tree',25000,'vegetation','jacaranda_tree'),('shrub_03',12000,'vegetation','shrub_03'),('street_lamp_02',30000,'street','polyhaven_street_lamp_02')]:
    output=P/'assets'/category/folder/(aid+'_optimized.blend')
    if output.exists(): print('CACHED',output,flush=True); continue
    source=P/'assets'/category/folder/(aid+'_1k.gltf')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bpy.context.view_layer.update()
    for o in objs:
        world=o.matrix_world.copy(); o.parent=None; o.matrix_world=world
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.join(); obj=bpy.context.object; obj.name='ASSET_'+aid
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    tris=sum(len(p.vertices)-2 for p in obj.data.polygons)
    print('OPTIMIZING',aid,tris,flush=True)
    if tris>budget:
        dec=obj.modifiers.new('LOD_Decimate','DECIMATE'); dec.ratio=budget/tris
        bpy.ops.object.modifier_apply(modifier=dec.name)
    verts=[v.co.copy() for v in obj.data.vertices]
    lower=Vector(tuple(min(v[i] for v in verts) for i in range(3)))
    upper=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
    origin=Vector(((lower.x+upper.x)/2,(lower.y+upper.y)/2,lower.z))
    height=upper.z-lower.z
    for v in obj.data.vertices: v.co=(v.co-origin)/height
    obj.location=(0,0,0)
    for p in obj.data.polygons: p.use_smooth=True
    obj['source_url']='https://polyhaven.com/a/'+aid; obj['license']='CC0'; obj['native_height_m']=height
    obj['source_triangles']=tris; obj['optimized_triangles']=sum(len(p.vertices)-2 for p in obj.data.polygons)
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath: im.pack()
    bpy.data.libraries.write(str(output),{obj},fake_user=True,compress=True)
    report.append(dict(asset=aid,source_triangles=tris,optimized_triangles=obj['optimized_triangles'],height_m=height))
    print('ASSET_READY',report[-1],flush=True)
(P/'docs/ASSET_OPTIMIZATION.json').write_text(json.dumps(report,indent=2),encoding='utf8')
