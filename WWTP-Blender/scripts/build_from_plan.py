"""Generate the first full-plant white model from data/plan_extracted.json."""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))
from core.collections import ensure_tree, remove_collection
from core.scene_utils import configure_metric_units, clean_orphans
from core.materials import ensure_principled, ensure_pbr

def link(obj, collection):
    for old in list(obj.users_collection): old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

def cube(name, dims, loc, col, mat=None, rotation=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=(0,0,rotation))
    obj=bpy.context.object; obj.name=name; obj.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    link(obj,col)
    if mat: obj.data.materials.append(mat)
    return obj

def segment(name, a, b, width, height, z, col, mat):
    a,b=Vector(a),Vector(b); d=b-a
    return cube(name,(d.length,width,height),((a.x+b.x)/2,(a.y+b.y)/2,z+height/2),col,mat,math.atan2(d.y,d.x))

def wall_loop(prefix, pts, height, thickness, col, mat, closed=True):
    pairs=list(zip(pts,pts[1:])) + ([(pts[-1],pts[0])] if closed else [])
    return [segment(f"{prefix}_{i+1:03d}",a,b,thickness,height,0,col,mat) for i,(a,b) in enumerate(pairs)]

def slab_polygon(name, pts, z, col, mat):
    verts=[(x,y,z) for x,y in pts]; mesh=bpy.data.meshes.new(name+"_Mesh")
    mesh.from_pydata(verts,[],[list(range(len(verts)))]); mesh.materials.append(mat)
    obj=bpy.data.objects.new(name,mesh); col.objects.link(obj); return obj

def pipe_curve(name, pts, radius, z, col, mat):
    curve=bpy.data.curves.new(name+"_Curve",'CURVE'); curve.dimensions='3D'; curve.bevel_depth=radius; curve.bevel_resolution=2; curve.resolution_u=1
    spline=curve.splines.new('POLY'); spline.points.add(len(pts)-1)
    for p,(x,y) in zip(spline.points,pts): p.co=(x,y,z,1)
    obj=bpy.data.objects.new(name,curve); col.objects.link(obj); obj.data.materials.append(mat); return obj

def ring(name, center, outer_r, height, thickness, col, mat):
    verts=[]; faces=[]; n=64; inner=outer_r-thickness
    for z in (0,height):
        for r in (outer_r,inner):
            verts.extend([(center[0]+r*math.cos(2*math.pi*i/n),center[1]+r*math.sin(2*math.pi*i/n),z) for i in range(n)])
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,2*n+j,2*n+i),(n+i,3*n+i,3*n+j,n+j),(2*n+i,2*n+j,3*n+j,3*n+i)]
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(mat)
    obj=bpy.data.objects.new(name,mesh); col.objects.link(obj); return obj

def disk(name, center, radius, z, col, mat):
    n=64; verts=[(center[0],center[1],z)]+[(center[0]+radius*math.cos(2*math.pi*i/n),center[1]+radius*math.sin(2*math.pi*i/n),z) for i in range(n)]
    faces=[tuple(range(n+1))]; mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(mat)
    obj=bpy.data.objects.new(name,mesh); col.objects.link(obj); return obj

def label(text, loc, col):
    curve=bpy.data.curves.new("LABEL_"+text,'FONT'); curve.body=text; curve.align_x='CENTER'; curve.size=3.4; curve.extrude=0.06
    obj=bpy.data.objects.new("LABEL_"+text,curve); obj.location=(*loc,5.0); col.objects.link(obj); return obj

def import_gltf_collection(name, filepath):
    """Import once into an unlinked source collection for lightweight instances."""
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(filepath))
    imported=[obj for obj in bpy.data.objects if obj not in before]
    source=bpy.data.collections.new('ASSET_SOURCE_'+name)
    for obj in imported:
        for old in list(obj.users_collection): old.objects.unlink(obj)
        source.objects.link(obj)
    return source

def collection_instance(name, source, location, col, scale=1.0, rotation=0.0):
    obj=bpy.data.objects.new(name,None); obj.instance_type='COLLECTION'; obj.instance_collection=source
    obj.location=location; obj.scale=(scale,scale,scale); obj.rotation_euler[2]=rotation; col.objects.link(obj)
    return obj

def linked_cylinder_source(name, radius, depth, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=(0,0,depth/2))
    source=bpy.context.object; source.name=name+'_Source'; source.data.materials.append(material)
    for old in list(source.users_collection): old.objects.unlink(source)
    source.hide_render=True; source.hide_viewport=True
    return source

def linked_object(name, source, location, col):
    obj=bpy.data.objects.new(name,source.data); obj.location=location; col.objects.link(obj); return obj

def aerator_grid(name, rect, z, col, material):
    """Represent 1,500 diffusers as point instances: one source mesh, no mesh duplication."""
    xs=[p[0] for p in rect]; ys=[p[1] for p in rect]
    minx,maxx,miny,maxy=min(xs)+1.4,max(xs)-1.4,min(ys)+1.4,max(ys)-1.4
    nx,ny=50,30
    verts=[(minx+(maxx-minx)*i/(nx-1),miny+(maxy-miny)*j/(ny-1),z) for j in range(ny) for i in range(nx)]
    mesh=bpy.data.meshes.new(name+'_Points_Mesh'); mesh.from_pydata(verts,[],[])
    obj=bpy.data.objects.new(name,mesh); col.objects.link(obj)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.1145,depth=.045,location=(0,0,0))
    disc=bpy.context.object; disc.name=name+'_Disc_Source'; disc.data.materials.append(material)
    for old in list(disc.users_collection): old.objects.unlink(disc)
    group=bpy.data.node_groups.new(name+'_GeometryNodes','GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=group.nodes; links=group.links
    inp=nodes.new('NodeGroupInput'); out=nodes.new('NodeGroupOutput')
    info=nodes.new('GeometryNodeObjectInfo'); info.inputs['Object'].default_value=disc
    inst=nodes.new('GeometryNodeInstanceOnPoints')
    links.new(inp.outputs['Geometry'],inst.inputs['Points']); links.new(info.outputs['Geometry'],inst.inputs['Instance']); links.new(inst.outputs['Instances'],out.inputs['Geometry'])
    mod=obj.modifiers.new(name='Aerator Instances',type='NODES'); mod.node_group=group
    obj['instance_count']=1500; obj['disc_diameter_m']=0.229
    return obj

def setup_tree_instances(tree_col, locations, trunk_mat, leaf_mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.35,depth=2.4,location=(0,0,1.2)); trunk=bpy.context.object; trunk.name='TREE_Trunk_Source'; trunk.data.materials.append(trunk_mat); link(trunk,tree_col)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1.8,location=(0,0,3.3)); crown=bpy.context.object; crown.name='TREE_Crown_Source'; crown.data.materials.append(leaf_mat); link(crown,tree_col)
    trunk.hide_render=True; crown.hide_render=True; trunk.hide_viewport=True; crown.hide_viewport=True
    for i,(x,y) in enumerate(locations):
        a=bpy.data.objects.new(f"TREE_Trunk_{i+1:03d}",trunk.data); a.location=(x,y,1.2); tree_col.objects.link(a)
        b=bpy.data.objects.new(f"TREE_Crown_{i+1:03d}",crown.data); b.location=(x,y,3.3); tree_col.objects.link(b)

def build(render=True):
    data=json.loads((PROJECT/'data'/'plan_extracted.json').read_text(encoding='utf-8'))
    configure_metric_units(); remove_collection('WWTP'); cols=ensure_tree()
    site,roads,buildings,pretreat,primary,bio,secondary,disinfection = (cols[x] for x in ('SITE','ROADS','BUILDINGS','PRETREATMENT','PRIMARY','BIOLOGICAL','SECONDARY','DISINFECTION'))
    mroot=PROJECT/'assets'/'materials'
    concrete=ensure_pbr('MAT_Concrete',mroot/'concrete'/'polyhaven_concrete_2k'/'concrete_diff_2k.jpg',mroot/'concrete'/'polyhaven_concrete_2k'/'concrete_nor_gl_2k.jpg',mroot/'concrete'/'polyhaven_concrete_2k'/'concrete_rough_2k.jpg',scale=.16,fallback=(.46,.50,.52))
    asphalt=ensure_pbr('MAT_Asphalt',mroot/'asphalt'/'polyhaven_asphalt_floor_2k'/'asphalt_floor_diff_2k.jpg',mroot/'asphalt'/'polyhaven_asphalt_floor_2k'/'asphalt_floor_nor_gl_2k.jpg',mroot/'asphalt'/'polyhaven_asphalt_floor_2k'/'asphalt_floor_rough_2k.jpg',scale=.12,fallback=(.045,.055,.065))
    grass=ensure_pbr('MAT_Grass',mroot/'grass'/'polyhaven_grass_ground_2k'/'grass_ground_diff_2k.jpg',mroot/'grass'/'polyhaven_grass_ground_2k'/'grass_ground_nor_gl_2k.jpg',mroot/'grass'/'polyhaven_grass_ground_2k'/'grass_ground_rough_2k.jpg',scale=.10,fallback=(.075,.22,.075))
    water=ensure_principled('MAT_Water',(0.03,0.24,0.36),metallic=.05,roughness=.18)
    white=ensure_principled('MAT_Building',(0.72,0.76,0.79),roughness=.66); roof=ensure_principled('MAT_Roof',(0.18,0.22,0.26),roughness=.55)
    trunkmat=ensure_principled('MAT_Trunk',(0.12,0.055,0.02),roughness=1); leafmat=ensure_principled('MAT_Leaves',(0.03,0.16,0.04),roughness=.9)
    metal=ensure_pbr('MAT_Metal',mroot/'metal'/'polyhaven_metal_plate_2k'/'metal_plate_diff_2k.jpg',mroot/'metal'/'polyhaven_metal_plate_2k'/'metal_plate_nor_gl_2k.jpg',mroot/'metal'/'polyhaven_metal_plate_2k'/'metal_plate_rough_2k.jpg',scale=.35,fallback=(.28,.31,.34),metallic=.65)
    aerator_mat=ensure_principled('MAT_Aerator',(0.035,0.045,0.055),metallic=.15,roughness=.62)
    pipe_mats={
      'W-MAIN':ensure_principled('MAT_Pipe_Water',(0.04,0.32,0.62),metallic=.25,roughness=.3), 'RAS':ensure_principled('MAT_Pipe_RAS',(0.40,0.12,0.05),metallic=.2,roughness=.35),
      'IR':ensure_principled('MAT_Pipe_IR',(0.55,0.25,0.03),metallic=.2,roughness=.35), 'AIR':ensure_principled('MAT_Pipe_Air',(0.04,0.52,0.72),metallic=.3,roughness=.28),
      'SLUDGE':ensure_principled('MAT_Pipe_Sludge',(0.28,0.12,0.04),metallic=.15,roughness=.4), 'BYPASS':ensure_principled('MAT_Pipe_Bypass',(0.52,0.06,0.06),metallic=.2,roughness=.34)}
    cube('SITE_Base_001',(400,300,.3),(200,150,-.15),site,grass)
    entities=data['entities']; roads_e=[e for e in entities if e['layer']=='ROAD' and e['type']=='LWPOLYLINE']
    for i,e in enumerate(roads_e): slab_polygon(f"ROAD_Plant_{i+1:02d}",e['points'],.02,roads,asphalt)
    out=[e for e in entities if e['layer']=='STRUCT-OUT']; inner=[e for e in entities if e['layer']=='STRUCT-IN']
    rects=[e for e in out if e['type']=='LWPOLYLINE']; circles=[e for e in out if e['type']=='CIRCLE']
    bio_rects=[]
    for i,e in enumerate(rects):
        pts=e['points']; xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; cy=sum(ys)/len(ys); w=max(xs)-min(xs); h=max(ys)-min(ys)
        if 138 <= cy <= 235:
            col=bio if cy<190 else primary; prefix='A2O' if cy<190 else 'PRIMARY'
            wall_loop(f"TANK_{prefix}_{i+1:02d}",pts,4.5,.55,col,concrete); slab_polygon(f"WATER_{prefix}_{i+1:02d}",pts,.18,col,water)
            if cy<190: bio_rects.append(pts)
        elif cy < 45 or (115 <= cy <= 135) or (250 <= cy <= 275):
            col=disinfection if 270<=sum(xs)/len(xs)<=350 and cy<45 else buildings
            minx,maxx,miny,maxy=min(xs),max(xs),min(ys),max(ys)
            cube(f"BUILDING_Plan_{i+1:02d}",(w,h,7.0),((minx+maxx)/2,(miny+maxy)/2,3.5),col,white)
            cube(f"ROOF_Plan_{i+1:02d}",(w+.8,h+.8,.35),((minx+maxx)/2,(miny+maxy)/2,7.17),col,roof)
        else: wall_loop(f"STRUCT_Plan_{i+1:02d}",pts,3.5,.45,pretreat,concrete)
    for i,e in enumerate(circles):
        ring(f"CLARIFIER_T{i+1:02d}",e['center'],e['radius'],4.0,.55,secondary,concrete); disk(f"WATER_T{i+1:02d}",e['center'],e['radius']-.65,.16,secondary,water)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=2.2,depth=4.4,location=(*e['center'],2.2)); hub=bpy.context.object;hub.name=f"SCRAPER_Hub_{i+1:02d}";link(hub,cols['SCRAPERS']);hub.data.materials.append(white)
        segment(f"SCRAPER_Bridge_{i+1:02d}",e['center'],(e['center'][0]+e['radius']-.7,e['center'][1]),.65,.35,4.25,cols['SCRAPERS'],white)
    for i,e in enumerate(inner):
        if e['type']=='LINE': segment(f"DIVIDER_{i+1:03d}",e['start'],e['end'],.38,4.2,0,bio if 138<e['start'][1]<190 else primary,concrete)
    pipe_cols={'W-MAIN':cols['WASTEWATER'],'RAS':cols['SLUDGE_RETURN'],'IR':cols['INTERNAL_RECYCLE'],'AIR':cols['AIR'],'SLUDGE':cols['SLUDGE_RETURN'],'BYPASS':cols['WASTEWATER']}
    radii={'W-MAIN':.48,'RAS':.3,'IR':.28,'AIR':.22,'SLUDGE':.28,'BYPASS':.35}
    for layer in pipe_cols:
        seq=0
        for e in entities:
            if e['layer']!=layer or e['type']!='LWPOLYLINE' or e.get('closed') or len(e['points'])<2: continue
            seq+=1; pipe_curve(f"PIPE_{layer.replace('-','_')}_{seq:03d}",e['points'],radii[layer],1.15,pipe_cols[layer],pipe_mats[layer])
    for i,pts in enumerate(sorted(bio_rects,key=lambda p: sum(x for x,_ in p)/len(p))[:4]): aerator_grid(f"AERATOR_GRID_{i+1:02d}",pts,.28,cols['BLOWERS'],aerator_mat)

    # Explicitly licensed external detail assets, instanced rather than duplicated.
    ext=PROJECT/'assets'
    lamp_src=import_gltf_collection('StreetLamp02',ext/'street'/'polyhaven_street_lamp_02'/'street_lamp_02_1k.gltf')
    lamp_locations=[(20,y) for y in range(25,286,40)]+[(380,y) for y in range(25,286,40)]+[(x,20) for x in range(60,361,60)]+[(x,280) for x in range(60,361,60)]
    for i,(x,y) in enumerate(lamp_locations): collection_instance(f"LIGHT_Street_{i+1:03d}",lamp_src,(x,y,.02),cols['LIGHTING'],3.2,0 if x<200 else math.pi)
    valve_src=import_gltf_collection('KenneyValve',ext/'equipment'/'valves'/'kenney_factory_kit'/'pipe-large-valve.glb')
    valve_locations=[(78,211),(122,211),(178,211),(222,211),(278,211),(322,211),(103,104),(197,104),(303,104),(343,104),(308,46),(338,46)]
    for i,(x,y) in enumerate(valve_locations): collection_instance(f"VALVE_Generic_{i+1:03d}",valve_src,(x,y,1.15),cols['PUMPS'],1.15,math.pi/2)
    machine_src=import_gltf_collection('KenneyMachine',ext/'equipment'/'misc'/'kenney_factory_kit'/'machine-fortified.glb')
    for i in range(6): collection_instance(f"BLOWER_VisualProxy_{i+1:02d}",machine_src,(304+i*7,259,1.0),cols['BLOWERS'],2.0,0)
    pump_src=import_gltf_collection('KenneyPumpProxy',ext/'equipment'/'misc'/'kenney_factory_kit'/'machine.glb')
    for i in range(6): collection_instance(f"PUMP_RAS_VisualProxy_{i+1:02d}",pump_src,(42+i*12,105,1.0),cols['PUMPS'],1.4,math.pi/2)
    tank_src=linked_cylinder_source('TANK_Chemical_20m3',1.6,2.5,metal)
    for i,loc in enumerate(((318,31,0),(323,31,0))):
        tank=linked_object(f"TANK_Chemical_20m3_{i+1:02d}",tank_src,loc,cols['DOSING']); tank['working_volume_m3']=20.0; tank['asset_role']='visual_proxy'
    trees=[tuple(e['center']) for e in entities if e['layer']=='GREEN' and e['type']=='CIRCLE' and .8<e['radius']<2]
    setup_tree_instances(cols['VEGETATION'],trees,trunkmat,leafmat)
    labels=[('C1',(50,226)),('C2',(150,226)),('C3',(250,226)),('C4',(350,226)),('A2O-1',(50,163)),('A2O-2',(150,163)),('A2O-3',(250,163)),('A2O-4',(350,163))]
    labels += [(f'T{i+1}',c['center']) for i,c in enumerate(circles)]
    for text,loc in labels: label(text,loc,cols['REFERENCES'])
    scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=1600; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
    scene.world.color=(.025,.035,.05); scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(PROJECT/'renders'/'previews'/'plant_refined.png')
    bpy.ops.object.light_add(type='SUN',location=(200,150,350)); sun=bpy.context.object; sun.name='LIGHT_Sun_001';sun.data.energy=3.0;sun.rotation_euler=(math.radians(28),math.radians(-22),math.radians(32));link(sun,cols['LIGHTING'])
    bpy.ops.object.camera_add(location=(540,-410,390)); cam=bpy.context.object;cam.name='CAMERA_Plant_Isometric';target=Vector((200,150,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=52;scene.camera=cam;link(cam,cols['REFERENCES'])
    bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'blender'/'plant.blend'))
    if render: bpy.ops.render.render(write_still=True)
    clean_orphans(); bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'blender'/'plant.blend'))
    return {'objects':len(bpy.data.objects),'trees':len(trees),'render':scene.render.filepath}

if __name__=='__main__': print(build(True))
