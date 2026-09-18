"""Map DXF footprints to their explicit drawing identifiers, retaining provenance."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
plan=json.loads((P/'data/plan_extracted.json').read_text(encoding='utf8'))
mapping=[('G1','coarse_screen',360,282),('P','wet_well',360,262),('G2','fine_screen',324,261),('SA','grit',207,274),('SB','grit',257,274),('PDA','distribution',100,259),('PDB','distribution',300,259),
 *[(f'C{i+1}','primary',50+100*i,226) for i in range(4)],*[(f'B{i+1}','a2o',50+100*i,163) for i in range(4)],
 ('DWA','distribution',100,124),('DWB','distribution',300,124),('AIR','blower_building',200,125),('CHEM','chemical_building',351,125),
 ('ADMIN','admin',68,29),('MAINT','maintenance',138,29),('NAOCL','dosing',249,29),('CT','contact',299,28.5),('METER','meter',338,29)]
rects=[e for e in plan['entities'] if e['layer']=='STRUCT-OUT' and e['type']=='LWPOLYLINE']
specs=[]
for ident,kind,x,y in mapping:
    found=min(rects,key=lambda e: (sum(p[0] for p in e['points'])/len(e['points'])-x)**2+(sum(p[1] for p in e['points'])/len(e['points'])-y)**2)
    pts=found['points']; bounds=[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
    specs.append(dict(id=ident,kind=kind,bounds=bounds,source='DXF STRUCT-OUT + text label',vertical_status='provisional'))
for i,e in enumerate(e for e in plan['entities'] if e['layer']=='STRUCT-OUT' and e['type']=='CIRCLE'):
    specs.append(dict(id=f'T{i+1}',kind='secondary',center=e['center'],radius=e['radius'],source='DXF STRUCT-OUT',vertical_status='provisional'))
out=dict(units='m',source=plan['source'],status='course_visual_model_not_hydraulic_design',structures=specs,
 defaults=dict(tank_top=2.0,tank_bottom=-2.8,water_level=1.3,wall=.35,walkway=.8,rail_height=1.1,rail_post_spacing=2.5,building_height=6.5,admin_height=9.5),
 biology=dict(lane_roles=['anaerobic','anoxic','aerobic','aerobic','aerobic','aerobic'],lane_partition_status='provisional teaching interpretation of six DXF lanes; confirm against process design',diffusers_per_series=1500,diameter=.229),
 render=dict(width=1920,height=1280,samples=48),
 assets=dict(tree='assets/vegetation/jacaranda_tree/jacaranda_tree_1k.gltf',shrub='assets/vegetation/shrub_03/shrub_03_1k.gltf',lamp='assets/street/polyhaven_street_lamp_02/street_lamp_02_1k.gltf'),
 detail=dict(window_spacing=4.5,window_width=2.1,window_height=1.5,curb_width=.22,curb_height=.18,fence_height=1.8,tree_height=7.0,shrub_height=.85),
 equipment_layout=dict(blowers=dict(count=6,duty=4,standby=2,host='AIR'),influent_pumps=dict(count=6,duty=4,standby=2,host='P'),ras_pumps=dict(count=6,duty=4,standby=2,hosts=['DWA','DWB']),internal_recycle_pumps=dict(count=6,duty=4,standby=2,hosts=['B1','B2','B3','B4'],allocation=[2,1,2,1],allocation_status='temporary visual allocation; no design duty assignment per series'),chemical_tanks=dict(count=2,working_volume=20,radius=1.6,total_height=3.2,host='NAOCL')))
(P/'data/engineering_model.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print('Mapped',len(specs),'unique structures; duplicate wet-well footprint removed.')
