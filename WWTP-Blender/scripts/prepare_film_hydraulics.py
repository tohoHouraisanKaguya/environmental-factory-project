"""PDF-v2 process routing: pipes between units, two independent A/B trains."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];rows=[]
def pipe(key,src,dst,pts,d=.9,system='W',zone='secondary',shots=(),basis='PDF topology; unlabelled diameter retained as presentation assumption'):
 rows.append(dict(id=key,source=src,target=dst,points=pts,kind='pipe',width=d,system=system,zone=zone,shots=list(shots),basis=basis))
def flat(key,src,dst,pts,d=.9,z=-1,**kw):pipe(key,src,dst,[(x,y,z) for x,y in pts],d,**kw)
flat('inlet','INLET','G1',[(360,300),(360,284.15)],1.2,z=.2,zone='raw',basis='PDF north inlet DN1200')
flat('coarse_to_pump','G1','P',[(360,279.85),(360,271.8)],1.2,z=.2,zone='raw')
flat('pump_to_fine','P','G2',[(357.2,262),(343,262),(343,261),(334.9,261)],1.2,z=.2,zone='raw')
flat('fine_split','G2','SPLIT',[(313.1,261),(286,261)],1.2,z=.2,zone='raw')
pipe('split_riser','SPLIT','PRE_HEADER',[(286,261,.2),(286,261,-1),(286,282,-1)],1.2,zone='raw')
for name,east,west,wx,dw in [('SA',222,192,100,'PDA'),('SB',272,242,300,'PDB')]:
 flat(name+'_feed','PRE_HEADER',name,[(286,282),(east+2,282),(east+2,274),(east-.2,274)],1.2,zone='raw')
 pts=[(west+.2,274),(180,274),(180,264),(100,264),(100,262.5)] if name=='SA' else [(west+.2,274),(240,274),(240,264),(300,264),(300,261)]
 flat(name+'_out',name,dw,pts,1.2,zone='primary',basis='PDF A/B DN1200; envelope endpoints extended to actual walls')
for i in range(1,5):
 cx=50+100*(i-1);wx=100 if i<=2 else 300;pd='PDA' if i<=2 else 'PDB';dw='DWA' if i<=2 else 'DWB'
 flat(f'C{i}_feed',pd,f'C{i}',[(wx,255.4),(wx,250),(cx,250),(cx,233),(cx-27.8,233),(cx-27.8,226)],.9,zone='primary',basis='PDF north-side DN900; internal inlet leg to existing longitudinal basin')
 flat(f'C{i}_to_B{i}',f'C{i}',f'B{i}',[(cx+27.7,226),(cx,226),(cx,218.5),(cx,185.2),(cx+33.8,185.2),(cx+33.8,181.75)],.9,zone='primary',basis='PDF same-column north-to-south external connection')
 flat(f'B{i}_out',f'B{i}',dw,[(cx+33.8,144.25),(cx+33.8,140.8),(cx,140.8),(cx,134),(wx,134),(wx,126)],1.2,basis='PDF south biological outlet, paired collection to DWA/DWB')
 flat(f'RAS_{i}',dw,f'B{i}',[(wx,124),(wx,191),(cx+33.8,191),(cx+33.8,181.75)],.45,z=-1.7,system='RAS',zone='anaerobic')
 # Last aerobic lane -> anoxic lane after rotating the original biological internals by 180 degrees.
 pipe(f'IR_{i}',f'B{i}',f'B{i}',[(cx-33.8,141.5,-1.8),(cx-33.8,141.5,2.7),(cx-37,141.5,2.7),(cx-37,174,2.7),(cx-28,174,2.7),(cx-28,174,-1.7)],.4,'IR','anoxic',['recycle'])
 flat(f'primary_sludge_{i}',f'C{i}','SL_PRIMARY',[(cx-27.8,226),(cx-27.8,212),(0,212)],.3,z=-4.2,system='SL',zone='anaerobic')
for i,x in enumerate((34,78,122,166,234,278,322,366),1):
 wx=100 if i<=4 else 300;dw='DWA' if i<=4 else 'DWB';group='A' if i<=4 else 'B'
 pipe(f'T{i}_feed',dw,f'T{i}',[(wx,121,-1.4),(wx,105,-1.4),(x,105,-1.4),(x,80,-1.4),(x,80,.2)],.9,basis='PDF distribution DN900')
 pipe(f'T{i}_out',f'T{i}',f'EFF_{group}',[(x,63.4,.6),(x,61,.6),(x,61,-1),(x,52,-1)],.9)
 pipe(f'T{i}_sludge',f'T{i}',dw,[(x,80,-3.9),(x,112,-3.9),(wx,112,-3.9),(wx,124,-3.9),(wx,124,-1.7)],.4,'RAS','anaerobic')
flat('effluent_A','EFF_A','EFFLUENT',[(34,52),(270,52)],1.2,basis='PDF A effluent DN1200')
flat('effluent_B','EFF_B','EFFLUENT',[(234,52),(366,52)],1.2,basis='PDF B effluent DN1200')
flat('effluent_to_contact','EFFLUENT','CT_IN',[(270,52),(274,52),(274,29)],1.5,basis='PDF merged flow; routed outside NAOCL footprint, dosing is a separate branch')
for i,y in enumerate((24,33),1):
 flat(f'CT{i}_feed','CT_IN','CT',[(274,29),(274,y),(278,y),(278,20.725 if i==1 else 29.675)],.9)
 flat(f'CT{i}_out','CT','METER',[(278,27.325 if i==1 else 36.275),(320.5,27.325 if i==1 else 36.275),(320.5,y),(329,y),(332,y)],.9,z=.2)
 flat(f'meter_{i}_out','METER','OUTLET_HEADER',[(344.1,y),(352,y),(352,29)],.9,z=.2)
flat('outlet','OUTLET_HEADER','OUTFALL',[(352,29),(400,29)],1.5,z=.2,basis='PDF east boundary DN1500 at (400,29)')
pipe('external_outfall','OUTFALL','RIVER',[(400,29,.2),(408,29,-1),(470,29,-7),(476.85,29,-6.85)],1.5,basis='Existing external outfall extension, beyond PDF boundary')
flat('sludge_A','DWA','SL_BOUNDARY',[(100,124),(0,124)],.3,z=-2.3,system='SL',zone='anaerobic')
flat('sludge_B','DWB','SL_BOUNDARY',[(300,124),(0,124)],.3,z=-2.6,system='SL',zone='anaerobic')
pipe('emergency_bypass','G2','CT_IN',[(286,261,.2),(286,261,-2.1),(386,261,-2.1),(386,48,-2.1),(274,48,-2.1),(274,29,-2.1),(274,29,-1)],.9,system='OV',basis='PDF explicitly provisional: G2 after to CT before; normally closed, no active flow')
pipe('dosing','NAOCL','CT_IN',[(263,29,1),(274,29,1),(274,29,-1)],.08,'CHEM',basis='Separate dosing connection; main water does not enter chemical storage')
pipe('blower_air_main','AIR','AIR_MAIN',[(218,129.3,2.643397),(222,129.3,2.643397),(222,136,2.643397)],.4,'AIR','air')
pipe('air_distribution','AIR_MAIN','AIR_MAIN',[(13,136,2.643397),(387,136,2.643397)],.4,'AIR','air')
for i in range(1,5):
 cx=50+(i-1)*100
 for j,(x,y) in enumerate(((cx-14.35,170.025),(cx+34.65,162.525),(cx+34.65,155.025),(cx+34.65,147.525))):
  pipe(f'air_{i}_{j}','AIR_MAIN',f'B{i}',[(cx+37,136,2.643397),(cx+37,y,2.643397),(x,y,2.643397),(x,y,2.3)],.24,'AIR','air')
for row,y in enumerate((256,263)):
 for j,x in enumerate((354.2,357.2,360.2)):
  pipe(f'pump_branch_{row}_{j}','P','P',[(x,y,-1.6),(x,262,-1.6),(357.2,262,-1.6),(357.2,262,.2)] if x!=357.2 else [(x,y,-1.6),(x,262,-1.6),(x,262,.2)],.45,zone='raw')
for wx,dw in ((100,'DWA'),(300,'DWB')):
 for j,x in enumerate((wx-2.2,wx+2.2)):flat(f'ras_branch_{dw}_{j}',dw,dw,[(x,124),(wx,124)],.35,z=-1.7,system='RAS',zone='anaerobic')
for i in (1,3):
 cx=50+(i-1)*100;flat(f'IR_second_{i}',f'B{i}',f'B{i}',[(cx-32.6,141.5),(cx-33.8,141.5)],.35,z=-1.8,system='IR',zone='anoxic')
# Eliminate identical adjacent nodes; retain the PDF-documented provisional status.
for r in rows:r['points']=[p for j,p in enumerate(r['points']) if j==0 or p!=r['points'][j-1]]
cfg=dict(units='m',revision='PDF-v2 corrected',status='PDF main topology, labelled DN sizes and systems; unlabelled diameters and all pipe elevations remain presentation assumptions. NAOCL/main-line graphic overlap separated; no flow through chemical storage.',channel_wall=.22,channel_depth=1.8,freeboard=.55,pipe_wall=.035,routes=rows)
(R/'data/film_hydraulics.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
revision=dict(biology_rotation_degrees=180,screen_header_length=1.0,screen_floor_z=-1.12,screen_top_z=2.0,water_z=1.3,meter=dict(count=2,centers_y=[24,33],throat_width=1.5,floor_z=-.5,water_z=.5,top_z=1.2,wall=.2,sections=[[331.65,2.0],[334,2.0],[336.5,.75],[340,.75],[344.35,2.0]]),contact=dict(centers_y=[24,33],lane_width=2.0,baffle_thickness=.2,turn_opening=2.0,inlet_side='west',outlet_side='east',single_unit_detail='Existing four-pass cells retained; submerged outlet collector extends to east-side external connection; detailed hydraulic profile pending'))
(R/'data/drawing_revision.json').write_text(json.dumps(revision,indent=2),encoding='utf8')
print('PDF routes',len(rows))
