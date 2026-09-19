"""Correct unit interfaces without treating dashed maintenance envelopes as tank walls."""
import bpy,json,math,re
from pathlib import Path
from mathutils import Vector,Matrix
from film_geometry import MeshBatch
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'data/drawing_revision.json').read_text(encoding='utf8'))

def waves(name,rect,z,bottom,col,mat):
    x0,y0,x1,y1=rect;nx=max(2,math.ceil((x1-x0)/.5));ny=max(2,math.ceil((y1-y0)/.5));b=MeshBatch()
    b.v=[(x0+(x1-x0)*i/nx,y0+(y1-y0)*j/ny,z) for j in range(ny+1) for i in range(nx+1)]
    b.f=[(j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i) for j in range(ny) for i in range(nx)]
    boundary=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    nt=len(b.v);n=len(boundary);b.v.extend((b.v[k][0],b.v[k][1],bottom) for k in boundary)
    b.f.extend((boundary[i],nt+i,nt+(i+1)%n,boundary[(i+1)%n]) for i in range(n));b.f.append(tuple(reversed(range(nt,nt+n))))
    o=b.object(name,col,mat);o.shape_key_add(name='Basis')
    for trig in ('sin','cos'):
        key=o.shape_key_add(name=trig);key.slider_min=-1
        for i in range(nt):key.data[i].co.z+=.012*getattr(math,trig)((b.v[i][0]+b.v[i][1])*2.8)
        key.driver_add('value').driver.expression=('cos' if trig=='sin' else '-sin')+'((frame-1)*2*pi/80)'
    return o

def prepare(scene,curves):
    eng=json.loads((R/'data/engineering_model.json').read_text(encoding='utf8'));specs={s['id']:s for s in eng['structures']};col=bpy.data.collections.new('DRAWING_V2_UNITS');scene.collection.children.link(col);mat=bpy.data.materials['MAT_Concrete'];water=bpy.data.materials['MAT_Water10_raw'];changes=[]
    # Rotate each entire biological assembly inside its unchanged 70 x 45 m footprint.
    for i in range(1,5):
        cx=50+100*(i-1);cy=163;transform=Matrix.Translation((cx,cy,0))@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation((-cx,-cy,0))
        for o in list(scene.objects):
            if re.search(r'_B'+str(i)+r'(?:_|$)',o.name):
                o.matrix_world=transform@o.matrix_world
                if o.animation_data:
                    for fc in o.animation_data.drivers:
                        if fc.data_path=='location' and fc.array_index in (0,1):fc.driver.expression=f'{2*(cx if fc.array_index==0 else cy)}-({fc.driver.expression})'
                changes.append(o.name)
    # Turn the fine-screen moving assemblies to face the east-to-west water connection.
    for o in list(scene.objects):
        if not o.name.startswith(('SCREEN_G2_','RAKE_G2_')):continue
        lane=int(re.search(r'Chain([12])',o.name).group(1)) if 'Chain' in o.name else int(o.name.rsplit('_',1)[-1])
        old=(318.12 if lane==1 else 329.88,261,0);new=(324,258 if lane==1 else 264,0)
        o.matrix_world=Matrix.Translation(new)@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(tuple(-v for v in old))@o.matrix_world
        if o.animation_data and o.animation_data.action:
            o.animation_data.action=o.animation_data.action.copy()
            for fc in curves(o.animation_data.action):
                if fc.data_path=='location' and fc.array_index==1:
                    fc.array_index=0
                    for p in fc.keyframe_points:
                        p.co.y=585-p.co.y;p.handle_left.y=585-p.handle_left.y;p.handle_right.y=585-p.handle_right.y
    # Rebuild only the interior deck and water. The four perimeter walls remain closed.
    for sid in ('G1','G2'):
        targets=[o for o in scene.objects if o.name==f'STRUCT_{sid}_ChannelDeck_001' or o.name.startswith('LIQUID_'+sid+'_')]
        print('SCREEN_INTERIOR_REBUILD',sid,[o.name for o in targets],flush=True)
        for o in targets:bpy.data.objects.remove(o,do_unlink=True)
        x0,y0,x1,y1=specs[sid]['bounds'];t=.35;x0+=t;x1-=t;y0+=t;y1-=t;h=D['screen_header_length'];floor=D['screen_floor_z'];top=D['screen_top_z'];b=MeshBatch();b.box(((x0+x1)/2,(y0+y1)/2,floor-.12),(x1-x0,y1-y0,.24))
        if sid=='G1':
            lanes=[(354.96-.765,354.96+.765),(365.04-.765,365.04+.765)]
            for a,c in ((x0,lanes[0][0]),(lanes[0][1],lanes[1][0]),(lanes[1][1],x1)):b.box(((a+c)/2,(y0+y1)/2,(floor+top)/2),(c-a,y1-y0-2*h,top-floor))
            rects=[(x0,y0,x1,y0+h),(x0,y1-h,x1,y1)]+[(a,y0+h,c,y1-h) for a,c in lanes]
        else:
            lanes=[(258-1.075,258+1.075),(264-1.075,264+1.075)]
            for a,c in ((y0,lanes[0][0]),(lanes[0][1],lanes[1][0]),(lanes[1][1],y1)):b.box(((x0+x1)/2,(a+c)/2,(floor+top)/2),(x1-x0-2*h,c-a,top-floor))
            rects=[(x0,y0,x0+h,y1),(x1-h,y0,x1,y1)]+[(x0+h,a,x1-h,c) for a,c in lanes]
        b.object(f'STRUCT_{sid}_ChannelDeck_001',col,mat)
        for j,rect in enumerate(rects):waves(f'LIQUID_{sid}_Connected_{j:03}',rect,D['water_z'],floor,col,water)
    (R/'docs/DRAWING_UNIT_REVISION.json').write_text(json.dumps({'biological_objects_rotated':len(changes),'screen_perimeters':'four original walls retained; internal plenums, no external open headers','fine_screen_axis':'east-west'},indent=2),encoding='utf8')

def meter(scene):
    col=bpy.data.collections['DRAWING_V2_UNITS'];cfg=D['meter'];mat=bpy.data.materials['MAT_Concrete'];water=bpy.data.materials['MAT_Water10_secondary'];bpy.data.objects['LIQUID_METER_001'].hide_render=True
    for lane,cy in enumerate(cfg['centers_y'],1):
        sections=cfg['sections'];floor=cfg['floor_z'];top=cfg['top_z'];b=MeshBatch()
        for x,w in sections:b.v.extend([(x,cy-w,floor),(x,cy+w,floor)])
        b.f=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(sections)-1)];obj=b.object(f'FILM_MeterFloor_{lane}',col,mat);obj.modifiers.new('Floor thickness','SOLIDIFY').thickness=.2
        for side in (-1,1):
            b=MeshBatch()
            for x,w in sections:b.v.extend([(x,cy+side*w,floor),(x,cy+side*w,top)])
            b.f=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(sections)-1)];obj=b.object(f'FILM_MeterWall_{lane}_{side}',col,mat);obj.modifiers.new('Channel wall','SOLIDIFY').thickness=cfg['wall']
        b=MeshBatch()
        for x,w in sections:b.v.extend([(x,cy-w+.015,cfg['water_z']),(x,cy+w-.015,cfg['water_z'])])
        b.f=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(sections)-1)];o=b.object(f'FILM_WaterMeter_{lane:03}',col,water);o.shape_key_add(name='Basis');key=o.shape_key_add(name='Water ripple');key.slider_min=-1
        for j,v in enumerate(key.data):v.co.z+=.009*math.sin(j*1.7)
        key.driver_add('value').driver.expression='sin((frame-1)*.11)'
    (R/'docs/FILM_METER_VALIDATION.json').write_text(json.dumps({'type':'long-throated','count':cfg['count'],'throat_width_m':2*min(w for x,w in cfg['sections']),'required_throat_width_m':cfg['throat_width']},indent=2),encoding='utf8')
