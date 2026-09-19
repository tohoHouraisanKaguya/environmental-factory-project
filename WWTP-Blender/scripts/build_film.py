"""Build the self-contained film from the frozen environment checkpoint. Blender 5.2."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from film_geometry import MeshBatch
D=json.loads((R/'data/film.json').read_text(encoding='utf8'))

def curves(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                yield from bag.fcurves

def linear(block):
    if block.animation_data and block.animation_data.action:
        for fc in curves(block.animation_data.action):
            for p in fc.keyframe_points:p.interpolation='LINEAR'

def fade(material,shots):
    m=material.copy();n=m.node_tree.nodes;l=m.node_tree.links
    out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
    original=out.inputs['Surface'].links[0].from_socket
    mix=n.new('ShaderNodeMixShader');transparent=n.new('ShaderNodeBsdfTransparent')
    l.new(original,mix.inputs[1]);l.new(transparent.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    for sh in shots:
        for frame,value in [(1,0),(sh['reveal_start'],0),(sh['dry_start'],1),(sh['dry_end'],1),(sh['restore_end'],0),(D['frames'],0)]:
            mix.inputs[0].default_value=value;mix.inputs[0].keyframe_insert('default_value',frame=frame)
    if out.inputs['Volume'].is_linked:
        volume=out.inputs['Volume'].links[0].from_node
        if 'Density' in volume.inputs:
            density=volume.inputs['Density'];base=density.default_value
            for sh in shots:
                for frame,value in [(1,base),(sh['reveal_start'],base),(sh['dry_start'],0),(sh['dry_end'],0),(sh['restore_end'],base),(D['frames'],base)]:
                    density.default_value=value;density.keyframe_insert('default_value',frame=frame)
    linear(m.node_tree);return m

def mesh(name,b,mat,loc=(0,0,0)):
    o=b.object(name,col,mat);o.location=loc;return o

def rotor(name,loc,r,axis=2):
    b=MeshBatch();b.rod((0,0,-.08),(0,0,.08),r*.22,32)
    for i in range(8):
        a=i*math.tau/8;p=(r*.25*math.cos(a),r*.25*math.sin(a),0);q=(r*.95*math.cos(a+.35),r*.95*math.sin(a+.35),.07)
        k=len(b.v)
        shape=[(.23,-.045),(.90,-.06),(1,.015),(.48,.13)]
        for zz in (-.045,.045):
            for radial,tangent in shape:b.v.append((r*(radial*math.cos(a)-tangent*math.sin(a)),r*(radial*math.sin(a)+tangent*math.cos(a)),zz))
        b.f.extend(tuple(k+j for j in face) for face in ((3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)))
    o=mesh(name,b,metal,loc)
    if axis==1:o.rotation_euler.x=math.pi/2
    o.driver_add('rotation_euler',axis).driver.expression=f'2*pi*{D["speeds"]["blower_demo_rps" if axis==1 else "pump_demo_rps"]}*(frame-1)/24'
    fixed=MeshBatch();fixed.rod((0,0,-.48),(0,0,-.14),r*.5,32);fixed.rod((0,0,-.15),(0,0,.10),r*.15,24)
    # Half casing retains the stationary housing and a readable inspection opening.
    for j in range(32):
        a0=math.pi*j/32;a1=math.pi*(j+1)/32;k=len(fixed.v)
        for zz in (-.12,.16):
            for rr,aa in ((r*1.08,a0),(r*1.22,a0),(r*1.22,a1),(r*1.08,a1)):fixed.v.append((rr*math.cos(aa),rr*math.sin(aa),zz))
        fixed.f.extend(tuple(k+v for v in face) for face in ((3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)))
    housing=mesh(name.replace('ROTOR','SECTION'),fixed,metal,loc)
    if axis==1:housing.rotation_euler.x=math.pi/2
    return o

def main():
    global s,col,metal
    bpy.ops.wm.open_mainfile(filepath=str(R/'blender/plant_environment_outfall.blend'))
    s=max(bpy.data.scenes,key=lambda x:len(x.objects));bpy.context.window.scene=s;s.name='FILM - 270 seconds'
    # Keep a single complete scene; source checkpoint retains all inspection scenes.
    for old in list(bpy.data.scenes):
        if old!=s:bpy.data.scenes.remove(old)
    col=bpy.data.collections.new('FILM_ADDITIONS');s.collection.children.link(col)
    s.frame_start=1;s.frame_end=D['frames'];s.render.fps=24
    s.render.resolution_x,s.render.resolution_y=D['resolution'];s.render.resolution_percentage=100
    s.render.engine='CYCLES';s.cycles.samples=D['samples'];s.cycles.use_denoising=True;s.cycles.adaptive_threshold=D['noise_threshold'];s.cycles.max_bounces=12;s.cycles.transmission_bounces=8;s.cycles.transparent_max_bounces=12
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8'
    s.render.film_transparent=False;s.render.use_motion_blur=False
    s.view_settings.view_transform='AgX'
    for o in s.objects:
        if o.type=='LIGHT':o.hide_render=True
    ld=bpy.data.lights.new('FILM_Sun','SUN');ld.energy=3;ld.angle=math.radians(3)
    sun=bpy.data.objects.new('FILM_Sun',ld);col.objects.link(sun);sun.rotation_euler=(.49,-.44,-.61)
    for n in s.world.node_tree.nodes:
        if n.type=='BACKGROUND':n.inputs['Strength'].default_value=.35
    # Continuous periodic actions beyond the old 240-frame demonstration.
    for action in bpy.data.actions:
        for fc in curves(action):
            if fc.keyframe_points and not any(m.type=='CYCLES' for m in fc.modifiers):fc.modifiers.new('CYCLES')
    for o in bpy.data.objects:
        if o.animation_data:
            for fc in o.animation_data.drivers:
                if o.name.startswith('ROTOR_Secondary'):fc.driver.expression='2*pi*(frame-1)/(24*100)'
                elif o.name.startswith(('SCRAPER_','BLADE_','LINK_')):fc.driver.expression=fc.driver.expression.replace('/240','/1920')
    # Subtle physical-size concrete texture, without changing design geometry.
    for m in bpy.data.materials:
        if m.use_nodes and ('concrete' in m.name.lower()):
            bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
            if bs:
                noise=m.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=18
                bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.025
                m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs[0],bs.inputs['Normal'])
                bs.inputs['Roughness'].default_value=.78
    from drawing_revision import prepare as correct_units, meter as correct_meter
    correct_units(s,curves)
    metal=bpy.data.materials.get('MAT_StainlessProcess')
    report={'shots':[],'rotors':[],'source':'plant_environment_outfall.blend','assumptions':D['assumptions']}
    byid={x['id']:x for x in D['shots']}
    for o in list(s.objects):
        if o.name.startswith(('PUMP_INFLUENT','PUMP_IR','PUMP_RAS')):
            sh=byid['pumps' if o.name.startswith('PUMP_INFLUENT') else 'recycle' if o.name.startswith('PUMP_IR') else 'distribution']
            r=min(o.dimensions.x,o.dimensions.y)*D['geometry']['pump_rotor_radius_fraction']
            rot=rotor('FILM_ROTOR_'+o.name,tuple(o.location),r);report['rotors'].append(rot.name)
            o.data=o.data.copy()
            for i,m in enumerate(o.data.materials):o.data.materials[i]=fade(m,[sh])
        elif o.name.startswith('BLOWER_NX300'):
            loc=o.location+Vector(D['geometry']['blower_internal_offset'])
            rot=rotor('FILM_ROTOR_'+o.name,loc,D['geometry']['blower_rotor_radius'],1);report['rotors'].append(rot.name)
            o.data=o.data.copy()
            for i,m in enumerate(o.data.materials):o.data.materials[i]=fade(m,[byid['blowers']])
    # Excavate the landscape under the existing hydraulic structures; no tank dimensions change.
    eng=json.loads((R/'data/engineering_model.json').read_text(encoding='utf8'))
    cuts=MeshBatch()
    for spec in eng['structures']:
        if spec['kind'] in ('coarse_screen','fine_screen','wet_well','grit','distribution','primary','a2o','contact','meter','secondary'):
            if spec['kind']=='secondary':
                x,y=spec['center'];cuts.rod((x,y,-12),(x,y,3),spec['radius']-.12,96);continue
            x0,y0,x1,y1=spec['bounds']
            if spec['kind']=='contact':
                center_y=(y0+y1)/2;p=json.loads((R/'data/process_detail.json').read_text(encoding='utf8'));c=p['contact'];width=c['cells']*(c['lanes_per_cell']*c['net_lane_width']+(c['lanes_per_cell']-1)*c['baffle_thickness'])+p['construction']['wall'];y0=center_y-width/2;y1=center_y+width/2
            cuts.box(((x0+x1)/2,(y0+y1)/2,-4.5),(x1-x0-.15,y1-y0-.15,15))
    cutter=mesh('FILM_ExcavationTool',cuts,None)
    ground=bpy.data.objects['SITE_Ground_001'];bpy.context.view_layer.objects.active=ground
    print('EXCAVATE_SITE',flush=True)
    mod=ground.modifiers.new('Hydraulic structure excavation','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='MANIFOLD';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print('EXCAVATE_TERRAIN',flush=True)
    earth=MeshBatch();earth.box((200,150,-5),(440,340,20));earthcut=mesh('FILM_TerrainTool',earth,None)
    ground=bpy.data.objects['TERRAIN_RiverValley_001'];bpy.context.view_layer.objects.active=ground
    mod=ground.modifiers.new('Terrain below developed site','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=earthcut
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(earthcut,do_unlink=True)
    print('EXCAVATION_COMPLETE',flush=True)
    bpy.data.objects.remove(cutter,do_unlink=True)
    correct_meter(s)
    # Camera travels inside the room; remove the architectural envelope for this shot only.
    for o in s.objects:
        if o.name.startswith(('ROOF_AIR','FACADE_AIR','GLAZING_AIR','DOOR_AIR','MULLION_AIR')):
            sh=byid['blowers']
            for f,v in [(1,False),(sh['start']-1,False),(sh['start'],True),(sh['end'],True),(sh['end']+1,False)]:o.hide_render=v;o.keyframe_insert('hide_render',frame=f)
    # Outfall stream: animated narrow discharge ribbon follows the existing apron.
    a=Vector(D['geometry']['outfall_start']);end=Vector(D['geometry']['outfall_end']);b=MeshBatch()
    for i in range(49):
        t=i/48;p=a.lerp(end,t);p.z+=.45*math.sin(math.pi*t)
        b.v.extend([(p.x,p.y-.10-.55*t,p.z),(p.x,p.y+.10+.55*t,p.z)])
    b.f=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(48)]
    water=bpy.data.materials.get('MAT_Water10_secondary');o=mesh('FILM_WaterOutfall_001',b,water)
    o.shape_key_add(name='Basis');key=o.shape_key_add(name='Ripples');key.slider_min=-1
    for i,v in enumerate(key.data):v.co.z+=.05*math.sin(i*.65)
    key.driver_add('value').driver.expression='sin((frame-1)*.25)'
    from film_hydraulics import build as connect_hydraulics, bore_pipe_routes, unify_channel_water
    connect_hydraulics(s,D['shots'],fade)
    bore_pipe_routes(s)
    unify_channel_water(s,D['shots'],fade)
    # Reveal materials are local to the corresponding objects, preserving adjacent wet tanks.
    for sh in D['shots']:
        targets=[o for o in s.objects if any(o.name.startswith(p) for p in sh['water'])]
        assert not sh['water'] or targets,sh['id']
        for o in targets:
            if o.get('film_fade_done'):continue
            relevant=[q for q in D['shots'] if any(o.name.startswith(p) for p in q['water'])]
            o.data=o.data.copy()
            for i,m in enumerate(o.data.materials):o.data.materials[i]=fade(m,relevant)
            o['film_fade_done']=True
        cd=bpy.data.cameras.new('FILM_CAM_'+sh['id']);cam=bpy.data.objects.new(cd.name,cd);col.objects.link(cam)
        cd.lens=sh['lens'];cd.clip_start=.05;cd.clip_end=15000
        # Sample smooth camera targeting to avoid Euler wrap at oblique views.
        previous=None
        for f in list(range(sh['start'],sh['end']+1,12))+[sh['end']]:
            t=(f-sh['start'])/(sh['end']-sh['start']);t=t*t*(3-2*t)
            cam.location=Vector(sh['camera_start']).lerp(Vector(sh['camera_end']),t)
            target=Vector(sh['target_start']).lerp(Vector(sh['target_end']),t)
            rot=(target-cam.location).to_track_quat('-Z','Y').to_euler()
            if previous is not None:rot.make_compatible(previous)
            previous=rot.copy();cam.rotation_euler=rot
            cam.keyframe_insert('location',frame=f);cam.keyframe_insert('rotation_euler',frame=f)
        linear(cam)
        marker=s.timeline_markers.new(sh['title'],frame=sh['start']);marker.camera=cam
        report['shots'].append({'id':sh['id'],'water_objects':[o.name for o in targets],'start':sh['start'],'end':sh['end']})
    s.camera=bpy.data.objects['FILM_CAM_overview'];s.frame_set(1)
    # All external image resources are embedded. Render runner adds captions to frames.
    bpy.ops.file.pack_all()
    for im in bpy.data.images:
        if im.packed_file:im.filepath='//packed/'+Path(im.filepath).name
    s.render.filepath='//../renders/film/raw/'
    s['film_assumptions']=json.dumps(D['assumptions']);s['captions']='Added by render_film.py using supplied PNG overlays'
    bpy.ops.wm.save_as_mainfile(filepath=str(R/'blender/plant_film.blend'),compress=True)
    (R/'docs/FILM_BUILD.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('FILM_BUILD_OK',len(report['shots']),len(report['rotors']))
if __name__=='__main__':main()
