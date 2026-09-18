"""Build a detailed, animation-ready WWTP model from engineering_model.json.

Horizontal geometry comes from the supplied DXF. Unconfirmed vertical dimensions
and A2/O lane roles remain explicitly marked as provisional in object metadata.
"""
from __future__ import annotations
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent; PROJECT=HERE.parent
sys.path.insert(0,str(HERE))
from core.collections import ensure_tree
from core.scene_utils import configure_metric_units, clean_orphans
from core.materials import ensure_principled, ensure_pbr

ENG=json.loads((PROJECT/'data/engineering_model.json').read_text(encoding='utf8'))
PLAN=json.loads((PROJECT/'data/plan_extracted.json').read_text(encoding='utf8'))
D=ENG['defaults']; random.seed(20260918)

def move(obj,col):
    for old in list(obj.users_collection): old.objects.unlink(obj)
    col.objects.link(obj); return obj

def cube(name,dims,loc,col,mat=None,rot=0):
    bpy.ops.mesh.primitive_cube_add(location=loc,rotation=(0,0,rot)); o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); move(o,col)
    if mat:o.data.materials.append(mat)
    return o

def cyl(name,r,depth,loc,col,mat=None,vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc); o=bpy.context.object;o.name=name;move(o,col)
    if mat:o.data.materials.append(mat)
    return o

def seg(name,a,b,width,height,z,col,mat):
    a,b=Vector(a),Vector(b); d=b-a
    return cube(name,(d.length,width,height),((a.x+b.x)/2,(a.y+b.y)/2,z+height/2),col,mat,math.atan2(d.y,d.x))

def rect(spec):
    x0,y0,x1,y1=spec['bounds']; return x0,y0,x1,y1,x1-x0,y1-y0,(x0+x1)/2,(y0+y1)/2

def mat_simple(name,color,rough=.55,metal=0): return ensure_principled(name,color,metal,rough)

def make_water(name,color):
    m=ensure_principled(name,color,metallic=.08,roughness=.16); bs=m.node_tree.nodes.get('Principled BSDF')
    if 'Coat Weight' in bs.inputs: bs.inputs['Coat Weight'].default_value=.35
    return m

def flat_poly(name,pts,z,col,mat):
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata([(x,y,z) for x,y in pts],[],[list(range(len(pts)))]); me.materials.append(mat)
    o=bpy.data.objects.new(name,me); col.objects.link(o); return o

def box_tank(spec,col,concrete,water,rail,walk=True):
    x0,y0,x1,y1,w,h,cx,cy=rect(spec); wall=D['wall']; top=D['tank_top']; bottom=D['tank_bottom']; wl=D['water_level']
    cube(f"SLAB_{spec['id']}_001",(w,h,.35),(cx,cy,bottom+.175),col,concrete)
    cube(f"WALL_{spec['id']}_N",(w,wall,top-bottom),(cx,y1-wall/2,(top+bottom)/2),col,concrete)
    cube(f"WALL_{spec['id']}_S",(w,wall,top-bottom),(cx,y0+wall/2,(top+bottom)/2),col,concrete)
    cube(f"WALL_{spec['id']}_E",(wall,h-2*wall,top-bottom),(x1-wall/2,cy,(top+bottom)/2),col,concrete)
    cube(f"WALL_{spec['id']}_W",(wall,h-2*wall,top-bottom),(x0+wall/2,cy,(top+bottom)/2),col,concrete)
    cube(f"LIQUID_{spec['id']}_001",(w-2*wall,h-2*wall,.12),(cx,cy,wl),col,water)
    if walk:
        ww=D['walkway']; cube(f"WALKWAY_{spec['id']}_N",(w+2*ww,ww,.16),(cx,y1+ww/2,top+.08),col,concrete)
        cube(f"WALKWAY_{spec['id']}_S",(w+2*ww,ww,.16),(cx,y0-ww/2,top+.08),col,concrete)
        cube(f"WALKWAY_{spec['id']}_E",(ww,h,.16),(x1+ww/2,cy,top+.08),col,concrete)
        cube(f"WALKWAY_{spec['id']}_W",(ww,h,.16),(x0-ww/2,cy,top+.08),col,concrete)
    for side,a,b in [('N',(x0,y1+D['walkway']), (x1,y1+D['walkway'])),('S',(x0,y0-D['walkway']),(x1,y0-D['walkway'])),('E',(x1+D['walkway'],y0),(x1+D['walkway'],y1)),('W',(x0-D['walkway'],y0),(x0-D['walkway'],y1))]:
        seg(f"RAIL_{spec['id']}_{side}_TOP",a,b,.055,.055,top+1.05,col,rail); seg(f"RAIL_{spec['id']}_{side}_MID",a,b,.045,.045,top+.55,col,rail)
        length=Vector(b).xy.__sub__(Vector(a).xy).length; count=max(2,int(length/2.5)+1)
        for i in range(count):
            t=i/(count-1); p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
            cyl(f"RAILPOST_{spec['id']}_{side}_{i:02d}",.035,1.1,(p[0],p[1],top+.55),col,rail,8)
    for o in [x for x in col.objects if spec['id'] in x.name]: o['engineering_verticals']='provisional'
    return x0,y0,x1,y1,w,h,cx,cy

def building(spec,col,wall,roof,glass,trim):
    x0,y0,x1,y1,w,h,cx,cy=rect(spec); height=D['admin_height'] if spec['kind']=='admin' else D['building_height']
    body=cube(f"BUILDING_{spec['id']}_Shell",(w,h,height),(cx,cy,height/2),col,wall); body['roof_can_hide_for_animation']=True
    cube(f"ROOF_{spec['id']}_001",(w+.7,h+.7,.35),(cx,cy,height+.175),col,roof)
    cube(f"PLINTH_{spec['id']}_001",(w+.25,h+.25,.55),(cx,cy,.275),col,trim)
    count=max(2,int((w-3)/4.5)); spacing=(w-4)/(count-1) if count>1 else 0
    for side,y,rot in [('S',y0-.012,0),('N',y1+.012,math.pi)]:
        for i in range(count):
            x=x0+2+i*spacing; cube(f"WINDOW_{spec['id']}_{side}_{i+1:02d}",(2.0,.08,1.55),(x,y,3.1),col,glass,rot)
    cube(f"DOOR_{spec['id']}_001",(1.8,.10,2.5),(cx,y0-.06,1.25),col,trim)
    return body

def screen_equipment(spec,col,metal,dark,fine=False):
    x0,y0,x1,y1,w,h,cx,cy=box_tank(spec,col,M['concrete'],M['water_raw'],metal)
    lanes=2
    for j in range(lanes):
        lx=x0+(j+.5)*w/lanes
        cube(f"SCREEN_{spec['id']}_Frame_{j+1}",(w/lanes-.5,.3,.3),(lx,cy,2.25),col,metal)
        bars=18 if fine else 10
        for i in range(bars):
            bx=x0+j*w/lanes+.35+(w/lanes-.7)*i/(bars-1)
            seg(f"SCREEN_{spec['id']}_Bar_{j+1}_{i+1}",(bx,y0+.5),(bx,y1-.5),.055,.055,.7,col,dark)

def grit_tank(spec,col):
    x0,y0,x1,y1,w,h,cx,cy=box_tank(spec,col,M['concrete'],M['water_raw'],M['rail'])
    seg(f"BRIDGE_{spec['id']}_001",(cx,y0-.7),(cx,y1+.7),1.15,.22,2.22,col,M['metal'])
    cyl(f"GRIT_{spec['id']}_Suction",.18,2.3,(cx,cy,1.0),col,M['dark'],16)

def primary_tank(spec,col):
    x0,y0,x1,y1,w,h,cx,cy=box_tank(spec,col,M['concrete'],M['water_primary'],M['rail'])
    for j in (1,2): cube(f"DIVIDER_{spec['id']}_{j}",(.28,h-1,.1),(x0+w*j/3,cy,D['tank_top']-.05),col,M['concrete'])
    seg(f"SCRAPER_{spec['id']}_Bridge",(x0-.8,cy),(x1+.8,cy),1.0,.25,2.25,col,M['metal'])
    for j in range(3):
        lx=x0+w*(j+.5)/3; seg(f"SCRAPER_{spec['id']}_Blade_{j+1}",(lx-7,cy),(lx+7,cy),.15,.7,-2.2,col,M['dark'])

def aerator_grid(name,bounds,col,mat):
    x0,y0,x1,y1=bounds; nx,ny=25,15; verts=[(x0+(x1-x0)*(i+.5)/nx,y0+(y1-y0)*(j+.5)/ny,-2.45) for j in range(ny) for i in range(nx)]
    me=bpy.data.meshes.new(name+'_Points'); me.from_pydata(verts,[],[]); obj=bpy.data.objects.new(name,me); col.objects.link(obj)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.1145,depth=.045); source=bpy.context.object; source.name=name+'_Source'; source.data.materials.append(mat)
    for old in list(source.users_collection): old.objects.unlink(source)
    ng=bpy.data.node_groups.new(name+'_GN','GeometryNodeTree'); ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry'); ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    inp=ng.nodes.new('NodeGroupInput'); out=ng.nodes.new('NodeGroupOutput'); info=ng.nodes.new('GeometryNodeObjectInfo'); info.inputs['Object'].default_value=source; inst=ng.nodes.new('GeometryNodeInstanceOnPoints')
    ng.links.new(inp.outputs['Geometry'],inst.inputs['Points']); ng.links.new(info.outputs['Geometry'],inst.inputs['Instance']); ng.links.new(inst.outputs['Instances'],out.inputs['Geometry'])
    obj.modifiers.new('Aerator Instances','NODES').node_group=ng; obj['instance_count']=nx*ny; return obj

def a2o(spec,col):
    x0,y0,x1,y1,w,h,cx,cy=box_tank(spec,col,M['concrete'],M['water_bio'],M['rail'])
    lane=h/6; roles=ENG['biology']['lane_roles']; colors=[M['water_anaerobic'],M['water_anoxic']]+[M['water_aerobic']]*4
    for j in range(6):
        ya=y0+j*lane; yb=ya+lane
        cube(f"ZONE_{spec['id']}_{roles[j]}_{j+1}",(w-.8,lane-.42,.10),(cx,(ya+yb)/2,D['water_level']+.04),col,colors[j])
        if j<5: cube(f"BAFFLE_{spec['id']}_{j+1}",(w-.7,.28,3.8),(cx,yb,(D['tank_bottom']+D['tank_top'])/2),col,M['concrete'])
        if j>=2: aerator_grid(f"AERATOR_{spec['id']}_LANE_{j+1}",(x0+.8,ya+.35,x1-.8,yb-.35),col,M['aerator'])
    # Six compact internal recycle pump visual proxies across four series allocation.
    count=ENG['equipment_layout']['internal_recycle_pumps']['allocation'][int(spec['id'][1])-1]
    for i in range(count):
        cyl(f"PUMP_IR_{spec['id']}_{i+1}",.45,1.0,(x1-1.2-i*1.2,y1-1.0,-1.8),col,M['pump'],20)

def circular_clarifier(spec,col):
    cx,cy=spec['center']; r=spec['radius']; top=D['tank_top']; bottom=D['tank_bottom']
    bpy.ops.mesh.primitive_torus_add(major_radius=r-D['wall']/2,minor_radius=D['wall']/2,major_segments=72,minor_segments=8,location=(cx,cy,top)); wall=bpy.context.object; wall.name=f"WALL_{spec['id']}_Rim"; move(wall,col); wall.data.materials.append(M['concrete'])
    cyl(f"LIQUID_{spec['id']}_001",r-.45,.10,(cx,cy,D['water_level']),col,M['water_secondary'],72)
    cyl(f"CENTER_{spec['id']}_Column",1.15,top-bottom,(cx,cy,(top+bottom)/2),col,M['concrete'],32)
    cyl(f"CENTER_{spec['id']}_FeedWell",3.0,.65,(cx,cy,D['water_level']+.15),col,M['metal'],48)
    seg(f"SCRAPER_{spec['id']}_Bridge",(cx-r-.4,cy),(cx+r+.4,cy),1.0,.26,top+.12,col,M['metal'])
    seg(f"SCRAPER_{spec['id']}_Arm",(cx,cy),(cx+r-1,cy),.18,.18,-2.25,col,M['dark'])
    for i in range(36):
        a=2*math.pi*i/36; cyl(f"RAILPOST_{spec['id']}_{i:02d}",.035,1.0,(cx+(r+.25)*math.cos(a),cy+(r+.25)*math.sin(a),top+.5),col,M['rail'],8)

def load_asset_data(blend_path,obj_name):
    with bpy.data.libraries.load(str(blend_path),link=False) as (src,dst): dst.objects=[obj_name]
    return bpy.data.objects[obj_name].data

def instance_mesh(name,data,loc,scale,col,rot=0):
    o=bpy.data.objects.new(name,data); o.location=loc;o.scale=(scale,scale,scale);o.rotation_euler[2]=rot;col.objects.link(o);return o

def point_instances(name,data,locations,scale,col):
    """Instance one linked mesh over a point set using a single Geometry Nodes object."""
    me=bpy.data.meshes.new(name+'_Points'); me.from_pydata([(x,y,z) for x,y,z in locations],[],[])
    obj=bpy.data.objects.new(name,me); col.objects.link(obj)
    source=bpy.data.objects.new(name+'_Source',data)
    ng=bpy.data.node_groups.new(name+'_GN','GeometryNodeTree'); ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry'); ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    inp=ng.nodes.new('NodeGroupInput');out=ng.nodes.new('NodeGroupOutput');info=ng.nodes.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=source
    inst=ng.nodes.new('GeometryNodeInstanceOnPoints');inst.inputs['Scale'].default_value=(scale,scale,scale)
    ng.links.new(inp.outputs['Geometry'],inst.inputs['Points']);ng.links.new(info.outputs['Geometry'],inst.inputs['Instance']);ng.links.new(inst.outputs['Instances'],out.inputs['Geometry'])
    obj.modifiers.new('Linked Instances','NODES').node_group=ng;obj['instance_count']=len(locations);return obj

def pipe_curve(name,pts,r,z,col,mat):
    cu=bpy.data.curves.new(name+'_Curve','CURVE'); cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,(x,y) in zip(sp.points,pts):p.co=(x,y,z,1)
    o=bpy.data.objects.new(name,cu);col.objects.link(o);cu.materials.append(mat);o['animation_medium']=name.split('_')[1];return o

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True);configure_metric_units();cols=ensure_tree();root=cols['WWTP']
    liquids=bpy.data.collections.new('LIQUIDS');cols['WATER_STRUCTURES'].children.link(liquids)
    guides=bpy.data.collections.new('ANIMATION_GUIDES');root.children.link(guides);guides.hide_render=True
    global M
    mr=PROJECT/'assets/materials'
    M={'concrete':ensure_pbr('MAT_Concrete',mr/'concrete/polyhaven_concrete_2k/concrete_diff_2k.jpg',mr/'concrete/polyhaven_concrete_2k/concrete_nor_gl_2k.jpg',mr/'concrete/polyhaven_concrete_2k/concrete_rough_2k.jpg',.18,(.58,.60,.59)),
       'asphalt':ensure_pbr('MAT_Asphalt',mr/'asphalt/polyhaven_asphalt_floor_2k/asphalt_floor_diff_2k.jpg',mr/'asphalt/polyhaven_asphalt_floor_2k/asphalt_floor_nor_gl_2k.jpg',mr/'asphalt/polyhaven_asphalt_floor_2k/asphalt_floor_rough_2k.jpg',.12,(.06,.07,.075)),
       'metal':ensure_pbr('MAT_Metal',mr/'metal/polyhaven_metal_plate_2k/metal_plate_diff_2k.jpg',mr/'metal/polyhaven_metal_plate_2k/metal_plate_nor_gl_2k.jpg',mr/'metal/polyhaven_metal_plate_2k/metal_plate_rough_2k.jpg',.3,(.3,.32,.34),.65),
       'grass':mat_simple('MAT_Grass_Lush',(.07,.28,.055),.92),'rail':mat_simple('MAT_Rail',(.78,.82,.83),.25,.75),'dark':mat_simple('MAT_DarkMetal',(.035,.045,.052),.3,.75),
       'building':mat_simple('MAT_Building',(.72,.78,.76),.68),'roof':mat_simple('MAT_Roof',(.19,.30,.34),.48,.1),'glass':mat_simple('MAT_Glass',(.06,.22,.30),.18,.2),'trim':mat_simple('MAT_Trim',(.16,.20,.21),.5),
       'pump':mat_simple('MAT_Pump',(.04,.30,.52),.3,.65),'aerator':mat_simple('MAT_Aerator',(.025,.03,.035),.65),
       'water_raw':make_water('MAT_Water_Raw',(.055,.20,.22)),'water_primary':make_water('MAT_Water_Primary',(.05,.27,.31)),'water_bio':make_water('MAT_Water_Bio',(.04,.30,.35)),'water_secondary':make_water('MAT_Water_Secondary',(.035,.38,.48)),
       'water_anaerobic':make_water('MAT_Zone_Anaerobic',(.13,.20,.18)),'water_anoxic':make_water('MAT_Zone_Anoxic',(.07,.27,.26)),'water_aerobic':make_water('MAT_Zone_Aerobic',(.025,.39,.53))}
    cube('SITE_Ground_001',(440,340,.4),(200,150,-.22),cols['SITE'],M['grass'])
    roads=[e for e in PLAN['entities'] if e['layer']=='ROAD' and e['type']=='LWPOLYLINE']
    for i,e in enumerate(roads):
        flat_poly(f"ROAD_{i+1:02d}",e['points'],.02,cols['ROADS'],M['asphalt'])
        pairs=list(zip(e['points'],e['points'][1:]+[e['points'][0]]))
        for j,(a,b) in enumerate(pairs):seg(f"CURB_{i+1:02d}_{j+1}",a,b,.22,.18,.02,cols['ROADS'],M['concrete'])
    specs={s['id']:s for s in ENG['structures']}
    for s in ENG['structures']:
        k=s['kind']
        if k=='secondary': circular_clarifier(s,cols['SECONDARY'])
        elif k=='primary': primary_tank(s,cols['PRIMARY'])
        elif k=='a2o': a2o(s,cols['BIOLOGICAL'])
        elif k=='coarse_screen': screen_equipment(s,cols['SCREENS'],M['metal'],M['dark'],False)
        elif k=='fine_screen': screen_equipment(s,cols['SCREENS'],M['metal'],M['dark'],True)
        elif k=='grit': grit_tank(s,cols['PRETREATMENT'])
        elif k in ('blower_building','chemical_building','admin','maintenance','dosing'): building(s,cols['BUILDINGS'],M['building'],M['roof'],M['glass'],M['trim'])
        else: box_tank(s,cols['DISINFECTION'] if k in ('contact','meter') else cols['PRETREATMENT'],M['concrete'],M['water_secondary'] if k in ('contact','meter') else M['water_raw'],M['rail'])
    # Contact tank baffles, six influent pumps, six blowers, RAS pumps and chemical tanks.
    x0,y0,x1,y1,w,h,cx,cy=rect(specs['CT'])
    for i in range(1,7): cube(f"BAFFLE_CT_{i:02d}",(.28,h-1,3.7),(x0+w*i/7,cy,-.4),cols['DISINFECTION'],M['concrete'])
    for i in range(6): cyl(f"PUMP_INFLUENT_{i+1:02d}",.55,1.5,(354.2+(i%3)*3,256+(i//3)*7,-1.6),cols['PUMPS'],M['pump'],24)
    for i in range(6):
        x=185+i*5.8; cube(f"BLOWER_CENTRIFUGAL_{i+1:02d}",(4.0,2.1,2.2),(x,125,1.1),cols['BLOWERS'],M['metal']);cyl(f"BLOWER_INLET_{i+1:02d}",.65,1.0,(x-1.8,125,1.1),cols['BLOWERS'],M['dark'],24)
    for host in ('DWA','DWB'):
        x0,y0,x1,y1,w,h,cx,cy=rect(specs[host])
        for i in range(3): cyl(f"PUMP_RAS_{host}_{i+1}",.48,1.15,(cx-2.2+i*2.2,cy,-1.7),cols['PUMPS'],M['pump'],20)
    for i,x in enumerate((244.5,253.5)):cyl(f"TANK_NAOCL_20m3_{i+1}",1.6,3.2,(x,29,1.6),cols['DOSING'],M['metal'],40)
    # Existing process pipe alignments become independently animatable flow families.
    pipe_cfg={'W-MAIN':(cols['WASTEWATER'],.45,M['water_raw']),'RAS':(cols['SLUDGE_RETURN'],.28,mat_simple('MAT_RAS',(.34,.11,.04),.4,.2)),'IR':(cols['INTERNAL_RECYCLE'],.25,mat_simple('MAT_IR',(.55,.24,.025),.35,.2)),'AIR':(cols['AIR'],.20,mat_simple('MAT_AIR',(.025,.55,.78),.28,.3)),'SLUDGE':(cols['SLUDGE_RETURN'],.25,M['dark']),'BYPASS':(cols['WASTEWATER'],.32,mat_simple('MAT_Bypass',(.62,.04,.035),.35,.2))}
    for layer,(col,r,mat) in pipe_cfg.items():
        for i,e in enumerate(x for x in PLAN['entities'] if x['layer']==layer and x['type']=='LWPOLYLINE' and not x.get('closed') and len(x['points'])>1):pipe_curve(f"PIPE_{layer.replace('-','_')}_{i+1:03d}",e['points'],r,1.0,col,mat)
    # Optimized linked vegetation and CC0 lamp assets.
    tree_data=load_asset_data(PROJECT/'assets/vegetation/jacaranda_tree/jacaranda_tree_optimized.blend','ASSET_jacaranda_tree')
    shrub_data=load_asset_data(PROJECT/'assets/vegetation/shrub_03/shrub_03_optimized.blend','ASSET_shrub_03')
    lamp_data=load_asset_data(PROJECT/'assets/street/polyhaven_street_lamp_02/street_lamp_02_optimized.blend','ASSET_street_lamp_02')
    greens=[e['center'] for e in PLAN['entities'] if e['layer']=='GREEN' and e['type']=='CIRCLE' and .8<e['radius']<2]
    point_instances('TREE_Jacaranda_Instances',tree_data,[(x,y,0) for x,y in greens],6.4,cols['VEGETATION'])
    hedge=[]
    for x in range(22,380,9):hedge.extend([(x,205),(x,137)])
    point_instances('SHRUB_Hedge_Instances',shrub_data,[(x,y,0) for x,y in hedge],.85,cols['VEGETATION'])
    lamp_locations=[(18,y) for y in range(28,282,42)]+[(382,y) for y in range(28,282,42)]+[(x,51) for x in range(45,370,48)]+[(x,202) for x in range(45,370,48)]
    point_instances('LIGHT_Street_Instances',lamp_data,[(x,y,0) for x,y in lamp_locations],3.6,cols['LIGHTING'])
    # Future animation route: process sequence curves hidden from final still.
    route=[(360,282),(360,262),(324,261),(232,274),(200,259),(200,226),(200,163),(200,124),(200,80),(299,28.5),(338,29),(400,29)]
    flowmat=mat_simple('MAT_AnimationFlow',(.05,.65,1),.2,.1); pipe_curve('FLOW_Master_Process',route,.35,5.5,guides,flowmat)
    for idx,label in enumerate(('粗格栅','提升泵','细格栅','沉砂','初沉','A2O','二沉配水','二沉','接触消毒','计量出水')): root[f'process_stage_{idx+1:02d}']=label
    # Lighting, world and camera.
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1920;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(PROJECT/'renders/previews/plant_detailed.png');scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('WWTP_Daylight');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.14,.22,.34,1);bg.inputs['Strength'].default_value=.45
    bpy.ops.object.light_add(type='SUN',location=(200,150,380));sun=bpy.context.object;sun.name='LIGHT_Sun_Daylight';sun.data.energy=2.2;sun.data.angle=math.radians(4);sun.rotation_euler=(math.radians(30),math.radians(-25),math.radians(-35));move(sun,cols['LIGHTING'])
    bpy.ops.object.camera_add(location=(510,-405,380));cam=bpy.context.object;cam.name='CAMERA_Plant_Hero';target=Vector((200,150,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=53;scene.camera=cam;move(cam,cols['REFERENCES'])
    scene.view_settings.look='AgX - Medium High Contrast';scene.frame_start=1;scene.frame_end=600;scene.render.fps=30
    scene['design_status']='DXF horizontal geometry; provisional verticals pending formal design documents';scene['animation_ready']='liquids, pipes, equipment and guides separated'
    bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'blender/plant.blend'));bpy.ops.render.render(write_still=True);clean_orphans();bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'blender/plant.blend'))
    print({'objects':len(bpy.data.objects),'trees':len(greens),'render':scene.render.filepath})

if __name__=='__main__': build()
