"""Build continuous channels, hollow connecting pipes and real civil penetrations."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from film_geometry import MeshBatch
R=Path(__file__).resolve().parents[1]

def bounds(o):
    v=[o.matrix_world@Vector(p) for p in o.bound_box]
    return [min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]
def intersects(a,b):return all(a[0][i]<b[1][i] and b[0][i]<a[1][i] for i in range(3))
def prism(b,corners,z0,z1):
    k=len(b.v);b.v += [(x,y,z0) for x,y in corners]+[(x,y,z1) for x,y in corners]
    b.f.extend([tuple(k+i for i in q) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
def sections(points,width):
    pts=[Vector(p) for p in points];out=[]
    for i,p in enumerate(pts):
        before=(pts[i]-pts[i-1]).normalized() if i else (pts[1]-p).normalized()
        after=(pts[i+1]-p).normalized() if i<len(pts)-1 else before
        n1=Vector((-before.y,before.x,0));n2=Vector((-after.y,after.x,0));bis=(n1+n2).normalized()
        off=bis*(width/2/max(.2,bis.dot(n1)));out.append((p+off,p-off))
    return out

def build(scene,shots,fade):
    bpy.ops.object.select_all(action='DESELECT')
    cfg=json.loads((R/'data/film_hydraulics.json').read_text(encoding='utf8'));col=bpy.data.collections.new('FILM_HYDRAULIC_CONNECTIONS');scene.collection.children.link(col)
    concrete=bpy.data.materials.get('MAT_Concrete');pipe_mat=bpy.data.materials.get('MAT_DarkMetal');cuts=MeshBatch();channel_shell=MeshBatch();channel_void=MeshBatch();openings=[];records=[]
    original=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(('WALL_','STRUCT_','SHELL_','BAFFLE_'))]
    # Replace the old abstract DXF tubes with the explicitly connected system.
    for o in scene.objects:
        if o.name.startswith(('PIPE_INLET','PIPE_OUTLET','PIPE_WASTEWATER','PIPE_Bypass','PIPE_BYPASS','PIPE_INFLUENT','PIPE_EFFLUENT','PIPE_SLUDGE','PIPE_IR_','PIPE_AIR_')):o.hide_render=True
    for route in cfg['routes']:
        print('CONNECT',route['id'],flush=True)
        name=route['id'];pts=route['points'];w=route['width'];z=pts[0][2]
        wet=bpy.data.materials.get('MAT_Water10_'+route['zone']) if route['zone']!='air' else None
        localshots=[s for s in shots if s['id'] in route['shots']]
        if route['kind']=='channel':
            inner=sections(pts,w);outer=sections(pts,w+2*cfg['channel_wall']);shell=MeshBatch();liquid=MeshBatch()
            bottom=z-cfg['channel_depth'];top=z+cfg['freeboard']
            for i in range(len(pts)-1):
                a,b=inner[i],inner[i+1];oa,ob=outer[i],outer[i+1]
                quad=lambda seq:[(p.x,p.y) for p in seq]
                prism(shell,quad((oa[0],oa[1],ob[1],ob[0])),bottom-.22,bottom)
                prism(shell,quad((oa[0],a[0],b[0],ob[0])),bottom,top)
                prism(shell,quad((a[1],oa[1],ob[1],b[1])),bottom,top)
                prism(liquid,quad((a[0],a[1],b[1],b[0])),bottom+.01,z)
                prism(channel_void,quad((a[0],a[1],b[1],b[0])),bottom+.005,top+.3)
                # Cut all terrain under this channel, and road surface only inside its physical trench.
                prism(cuts,quad((oa[0],oa[1],ob[1],ob[0])),bottom-.5,top+.1)
            offset=len(channel_shell.v);channel_shell.v.extend(shell.v);channel_shell.f.extend(tuple(v+offset for v in f) for f in shell.f)
            water=liquid.object('FLOWING_'+name,col,fade(wet,localshots) if localshots else wet)
            for endpoint,neighbor in ((pts[0],pts[1]),(pts[-1],pts[-2])):
                direction=(Vector(neighbor)-Vector(endpoint)).normalized();center=Vector(endpoint)
                b=MeshBatch();size=(w+.08,2.0,cfg['channel_depth']+cfg['freeboard']+.1) if abs(direction.y)>.5 else (2.0,w+.08,cfg['channel_depth']+cfg['freeboard']+.1)
                b.box((center.x,center.y,(top+bottom)/2),size);openings.append(b.object('TEMP_Port_'+name,col,None))
        else:
            c=bpy.data.curves.new('PipePath_'+name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=w/2;c.bevel_resolution=4;c.use_fill_caps=False
            sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
            for q,p in zip(sp.points,pts):q.co=(*p,1)
            o=bpy.data.objects.new('CONDUIT_'+name,c);col.objects.link(o);c.materials.append(bpy.data.materials.get('MAT_AIR_Header') if route['zone']=='air' else pipe_mat)
            bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
            mod=o.modifiers.new('Hollow pipe wall','SOLIDIFY');mod.thickness=cfg['pipe_wall'];mod.offset=1
            # Entire pipe runs are bored in bore_pipe_routes; avoid redundant endpoint cutters.
            # Short concrete bearing pads for above-grade lines, below the pipe invert.
            pads=MeshBatch()
            for a,b in zip(pts,pts[1:]):
                a,b=Vector(a),Vector(b);length=(b-a).length
                if a.z>w/2+.4 and b.z>w/2+.4 and length>3:
                    for j in range(1,math.ceil(length/5)):
                        p=a.lerp(b,j/math.ceil(length/5));h=p.z-w/2-.1
                        pads.box((p.x,p.y,h/2),(.35,.35,h));pads.box((p.x,p.y,.08),(.7,.7,.16))
            if pads.v:pads.object('BEARING_'+name,col,concrete)
        records.append({'id':name,'source':route['source'],'target':route['target'],'kind':route['kind'],'point_count':len(pts),'system':route.get('system'),'diameter_m':w,'basis':route.get('basis')})
    gate=MeshBatch();gate.rod((386,149.95,-2.1),(386,150.05,-2.1),.45,32)
    valve=gate.object('VALVE_OV_Closed_001',col,pipe_mat);valve['normally_closed']=True;valve['system']='OV';valve['basis']='PDF provisional emergency bypass'
    if channel_shell.v:
        print('OPEN_CHANNEL_JUNCTIONS',flush=True)
        network=channel_shell.object('CHANNEL_Network_001',col,concrete);void=channel_void.object('TEMP_ChannelVoid',col,None)
        bpy.context.view_layer.objects.active=network
        mod=network.modifiers.new('Continuous wetted channel interior','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.use_self=True;mod.object=void
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(void,do_unlink=True)
    bpy.context.view_layer.update();changed=[]
    print('OPENING_CIVIL_PORTS',len(openings),flush=True)
    for cutter in openings:
        cb=bounds(cutter)
        for o in original:
            if intersects(bounds(o),cb):
                bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Connected flow opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.use_self=True;mod.object=cutter
                bpy.ops.object.modifier_apply(modifier=mod.name);changed.append(o.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
    if cuts.v:
        cutter=cuts.object('TEMP_ChannelExcavation',col,None);bpy.context.view_layer.update()
        for o in list(scene.objects):
            if o.type=='MESH' and (o.name=='SITE_Ground_001' or o.name.startswith(('ROAD_','CURB_'))):
                print('TRENCH',o.name,flush=True)
                bpy.context.view_layer.objects.active=o;mod=o.modifiers.new('Channel trench','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.use_self=True;mod.object=cutter
                bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
    repair_shared_secondary(scene)
    changed.extend(['STRUCT_SecondaryShell_001','TROUGH_SecondaryDoubleSided_001'])
    bpy.context.view_layer.update()
    blocked=[]
    for route in cfg['routes']:
        if route['kind']!='channel':continue
        for a,b in zip(route['points'],route['points'][1:]):
            p=Vector(a);q=Vector(b);p.z-=.3;q.z-=.3;v=q-p
            hit=network.ray_cast(p+v.normalized()*.02,v.normalized(),distance=max(.01,v.length-.04))
            if hit[0]:blocked.append(route['id'])
    assert not blocked,('Blocked channel centerlines',blocked)
    # Reachability proves declared coverage; visual QA separately checks geometry.
    graph={}
    for r in records:graph.setdefault(r['source'],set()).add(r['target'])
    reached={'INLET'}
    while True:
        new=reached|{b for a in reached for b in graph.get(a,())}
        if new==reached:break
        reached=new
    expected={'G1','P','G2','SA','SB','PDA','PDB','DWA','DWB','CT','METER','OUTFALL'}|{f'{prefix}{i}' for prefix,count in [('C',4),('B',4),('T',8)] for i in range(1,count+1)}
    assert expected<=reached,expected-reached
    report={'status':cfg['status'],'routes':records,'blocked_channel_centerlines':blocked,'civil_objects_opened':sorted(set(changed)),'reachable_process_nodes':sorted(reached),'missing_process_nodes':sorted(expected-reached)}
    (R/'docs/FILM_HYDRAULICS.json').write_text(json.dumps(report,indent=2),encoding='utf8')

def bore_pipe_routes(scene):
    """Bore wall crossings along entire pipe runs, including ports away from route endpoints."""
    cfg=json.loads((R/'data/film_hydraulics.json').read_text(encoding='utf8'))
    col=bpy.data.collections['FILM_HYDRAULIC_CONNECTIONS']
    walls=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(('WALL_','STRUCT_','SHELL_','BAFFLE_'))]
    changes=[]
    for route in cfg['routes']:
        if route['kind']!='pipe':continue
        print('BORE_CHECK',route['id'],flush=True)
        for a,b in zip(route['points'],route['points'][1:]):
            a,b=Vector(a),Vector(b);v=(b-a).normalized();batch=MeshBatch();batch.rod(a-v*.06,b+v*.06,route['width']/2+.035,32)
            cutter=batch.object('TEMP_PipeBore',col,None);bpy.context.view_layer.update();cb=bounds(cutter)
            for wall in walls:
                if not intersects(bounds(wall),cb):continue
                # Apply only when an actual centerline wall crossing remains.
                inv=wall.matrix_world.inverted();origin=inv@(a-v*.04);direction=(inv.to_3x3()@v).normalized()
                if not wall.ray_cast(origin,direction,distance=(inv.to_3x3()@v).length*((b-a).length+.08))[0]:continue
                bpy.context.view_layer.objects.active=wall;mod=wall.modifiers.new('Full connecting pipe bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.use_self=True;mod.object=cutter
                bpy.ops.object.modifier_apply(modifier=mod.name);changes.append({'route':route['id'],'wall':wall.name})
            bpy.data.objects.remove(cutter,do_unlink=True)
    bpy.context.view_layer.update();blocked=[]
    for route in cfg['routes']:
        if route['kind']!='pipe':continue
        for a,b in zip(route['points'],route['points'][1:]):
            a,b=Vector(a),Vector(b);v=(b-a).normalized()
            for wall in walls:
                inv=wall.matrix_world.inverted()
                hit=wall.ray_cast(inv@(a+v*.01),(inv.to_3x3()@v).normalized(),distance=((inv.to_3x3()@v).length)*((b-a).length-.02))
                if hit[0]:blocked.append({'route':route['id'],'wall':wall.name,'hit':list(wall.matrix_world@hit[1]),'scale':list(wall.scale)})
    if blocked:bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/debug_ports.blend'),compress=True)
    assert not blocked,blocked
    (R/'docs/FILM_PIPE_PORTS.json').write_text(json.dumps({'additional_wall_bores':changes,'blocked_pipe_centerlines':blocked},indent=2),encoding='utf8')

def unify_channel_water(scene,shots,fade):
    """Union overlapping channel volumes to remove double absorption at junctions."""
    cfg=json.loads((R/'data/film_hydraulics.json').read_text(encoding='utf8'));parent=bpy.data.collections['FILM_HYDRAULIC_CONNECTIONS'];report=[]
    for zone in sorted({r['zone'] for r in cfg['routes'] if r['kind']=='channel'}):
        routes=[r for r in cfg['routes'] if r['kind']=='channel' and r['zone']==zone]
        objects=[bpy.data.objects.get('FLOWING_'+r['id']) for r in routes];objects=[o for o in objects if o]
        if not objects:continue
        base=objects[0];temp=bpy.data.collections.new('TEMP_WaterUnion');scene.collection.children.link(temp)
        for o in objects[1:]:temp.objects.link(o)
        if len(objects)>1:
            bpy.context.view_layer.objects.active=base;mod=base.modifiers.new('Continuous channel water volume','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.operand_type='COLLECTION';mod.collection=temp;mod.use_self=True
            bpy.ops.object.modifier_apply(modifier=mod.name)
        for o in objects[1:]:bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(temp)
        shids={key for r in routes for key in r['shots']};material=fade(bpy.data.materials['MAT_Water10_'+zone],[s for s in shots if s['id'] in shids])
        base.data.materials.clear();base.data.materials.append(material)
        for poly in base.data.polygons:poly.material_index=0
        base.name='FLOWING_NETWORK_'+zone
        report.append({'zone':zone,'united_routes':len(routes),'polygons':len(base.data.polygons)})
    (R/'docs/FILM_CHANNEL_WATER.json').write_text(json.dumps(report,indent=2),encoding='utf8')

def repair_shared_secondary(scene):
    """Keep sloping floors separate from booleans on the shared clarifier wall."""
    cfg=json.loads((R/'data/online_detail_assets.json').read_text(encoding='utf8'))['secondary']
    td=json.loads((R/'data/secondary_detail.json').read_text(encoding='utf8'))
    library=bpy.data.collections['LIB_Secondary_D37'];work=bpy.data.collections['FILM_HYDRAULIC_CONNECTIONS'];mat=bpy.data.materials['MAT_Concrete']
    r=cfg['diameter']/2;ri=cfg['feedwell_diameter']/2;top=cfg['water_z']+cfg['freeboard'];floor=cfg['water_z']-cfg['peripheral_depth'];inner=floor-(r-ri)*cfg['slope']
    cutter_batch=MeshBatch();cutter_batch.rod((0,17.3,-1.4),(0,19.5,-1.4),.535,48);cutter_batch.rod((0,-16.25,.6),(0,-19.5,.6),.385,48)
    cutter=cutter_batch.object('TEMP_SecondaryBores',work,None)
    wall=MeshBatch();wall.ring(r,r+cfg['wall'],top,top,top-floor)
    obj=wall.object('TEMP_SecondaryWall',work,mat);bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Wall ports','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.use_self=True;mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
    shell=MeshBatch();shell.v=[tuple(v.co) for v in obj.data.vertices];shell.f=[tuple(p.vertices) for p in obj.data.polygons]
    shell.ring(ri,r,inner,floor,.30);shell.ring(.01,ri,inner-cfg['sump_depth'],inner-cfg['sump_depth'],.30);
    sump=MeshBatch();sump.ring(ri,ri+.2,inner,inner,cfg['sump_depth']);part=sump.object('TEMP_SumpWall',work,mat)
    bore=MeshBatch();bore.rod((0,0,-3.9),(0,ri+.4,-3.9),.235,32);hole=bore.object('TEMP_SumpPort',work,None);bpy.context.view_layer.objects.active=part
    mod=part.modifiers.new('Sludge suction port','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=hole;bpy.ops.object.modifier_apply(modifier=mod.name)
    offset=len(shell.v);shell.v.extend(tuple(v.co) for v in part.data.vertices);shell.f.extend(tuple(v+offset for v in f.vertices) for f in part.data.polygons);bpy.data.objects.remove(part,do_unlink=True);bpy.data.objects.remove(hole,do_unlink=True)
    shell.ring(r+cfg['wall'],r+cfg['wall']+cfg['walkway'],top,top,.25)
    result=shell.object('TEMP_SecondaryShellResult',work,mat);target=bpy.data.objects['STRUCT_SecondaryShell_001'];target.data=result.data
    bpy.data.objects.remove(result,do_unlink=True);bpy.data.objects.remove(obj,do_unlink=True)
    rc=td['weir_centerline_diameter_m']/2;half=td['trough_width_m']/2;a,b=rc-half,rc+half;t=td['concrete_thickness_m'];crest=cfg['water_z']+.07;base=crest-td['trough_depth_m'];wt=crest-.22
    combined=MeshBatch()
    for args in [(a,b,base,base,t),(a,a+t,wt,wt,wt-base),(b-t,b,wt,wt,wt-base)]:
        batch=MeshBatch();batch.ring(*args,n=384);part=batch.object('TEMP_LaunderPart',work,mat);bpy.context.view_layer.objects.active=part
        mod=part.modifiers.new('Launder outlet','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.use_self=True;mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name)
        offset=len(combined.v);combined.v.extend(tuple(v.co) for v in part.data.vertices);combined.f.extend(tuple(v+offset for v in p.vertices) for p in part.data.polygons);bpy.data.objects.remove(part,do_unlink=True)
    result=combined.object('TEMP_LaunderResult',work,mat);bpy.data.objects['TROUGH_SecondaryDoubleSided_001'].data=result.data;bpy.data.objects.remove(result,do_unlink=True);bpy.data.objects.remove(cutter,do_unlink=True)
    # Confirm the floor really exists at several radii, not merely a parsable mesh.
    bpy.context.view_layer.update();hits=[]
    for x in (4,9,16):
        hit=target.ray_cast(Vector((x,0,5)),Vector((0,0,-1)))
        assert hit[0] and -4<hit[1].z<-2,(x,hit)
        hits.append([x,hit[1].z])
    (R/'docs/FILM_SECONDARY_FLOOR.json').write_text(json.dumps({'floor_ray_hits':hits,'shared_by_tanks':8},indent=2),encoding='utf8')
