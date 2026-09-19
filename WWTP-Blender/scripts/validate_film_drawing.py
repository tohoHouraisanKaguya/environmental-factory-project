"""Inspect the saved film's screen corners, meter mesh and pipeline configuration."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'blender/plant_film.blend'))
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
eng=json.loads((R/'data/engineering_model.json').read_text(encoding='utf8'));cfg=json.loads((R/'data/film_hydraulics.json').read_text(encoding='utf8'))
checks=[]
for sid in ('G1','G2'):
    spec=next(x for x in eng['structures'] if x['id']==sid);x0,y0,x1,y1=spec['bounds']
    walls=[o for o in s.objects if o.name.startswith('WALL_'+sid+'_')]
    for ix,x in enumerate((x0+.12,x1-.12)):
        for iy,y in enumerate((y0+.12,y1-.12)):
            hit=False
            for wall in walls:
                inv=wall.matrix_world.inverted();a=inv@Vector((x,y,3));v=inv.to_3x3()@Vector((0,0,-1))
                hit=hit or wall.ray_cast(a,v.normalized(),distance=2*v.length)[0]
            checks.append(dict(check=f'{sid}_corner_{ix}{iy}',passed=bool(hit)))
    for water in [o for o in s.objects if o.name.startswith('LIQUID_'+sid+'_Connected')]:
        pts=[water.matrix_world@v.co for v in water.data.vertices]
        checks.append(dict(check=water.name+'_contained',passed=all(x0<=p.x<=x1 and y0<=p.y<=y1 for p in pts)))
for lane in (1,2):
    left=bpy.data.objects[f'FILM_MeterWall_{lane}_-1'];right=bpy.data.objects[f'FILM_MeterWall_{lane}_1']
    widths=[abs((left.matrix_world@left.data.vertices[i].co).y-(right.matrix_world@right.data.vertices[i].co).y) for i in range(0,len(left.data.vertices),2)]
    checks.append(dict(check=f'meter_{lane}_throat_1_50m',passed=abs(min(widths)-1.5)<1e-5,measured=min(widths)))
checks.append(dict(check='no_external_open_channel_network',passed=not any(o.name.startswith('CHANNEL_Network') for o in s.objects)))
checks.append(dict(check='all_102_declared_pipes_exist',passed=len(cfg['routes'])==102 and all(bpy.data.objects.get('CONDUIT_'+r['id']) for r in cfg['routes'])))
checks.append(dict(check='required_pipe_systems',passed={'W','RAS','IR','SL','AIR','OV','CHEM'}<={r['system'] for r in cfg['routes']}))
for i in range(1,5):
    feed=next(r for r in cfg['routes'] if r['id']==f'C{i}_to_B{i}');out=next(r for r in cfg['routes'] if r['id']==f'B{i}_out')
    checks.append(dict(check=f'B{i}_north_in_south_out',passed=feed['points'][-1][1]>163 and out['points'][0][1]<163))
result=dict(checks=checks,passed=all(c['passed'] for c in checks))
(R/'docs/FILM_DRAWING_VALIDATION.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result));assert result['passed']
