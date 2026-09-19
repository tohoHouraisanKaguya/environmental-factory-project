"""Create portable, declarative shot list and raster Chinese captions (no Blender needed)."""
import json, argparse, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/video_captions'
OUT.mkdir(parents=True, exist_ok=True)
# Camera endpoints and targets in metres; 24 fps; all wet shots have continuous reveal.
ROWS = [
 ('overview','污水处理厂',18,(660,-410,520),(570,-310,410),(210,150,0),(220,165,0),[],34),
 ('coarse','粗格栅',14,(377,267,24),(369,270,17),(360,282,1),(360,282,1),['LIQUID_G1'],46),
 ('pumps','进水提升泵站',16,(378,241,23),(364,249,13),(360,260,0),(357,259,-.5),['LIQUID_P_'],43),
 ('fine','细格栅',12,(345,244,23),(335,248,16),(324,261,1),(324,261,1),['LIQUID_G2'],46),
 ('grit','曝气沉砂池',16,(226,259,15),(214,266,11),(208,274,.5),(203,274,.2),['LIQUID_SA_'],43),
 ('primary','初沉池',22,(90,195,36),(55,207,22),(50,226,0),(40,226,-.3),['LIQUID_C1_'],42),
 ('anaerobic','厌氧池',16,(43,127,18),(35,136,10),(35,144.5,-.2),(30,144.5,-1.2),['LIQUID_B1_anaerobic'],43),
 ('anoxic','缺氧池',16,(57,137,17),(44,145,11),(43,153,-.2),(38.3,152,-1.2),['LIQUID_B1_anoxic'],43),
 ('blowers','鼓风机房',18,(202,118.8,6),(187,121,3.5),(196.6,125,1.6),(185,125,1.4),[],38),
 ('aerobic','好氧池 · 曝气系统',20,(83,160,26),(66,169,13),(59,175,.2),(59,175,-1.2),['LIQUID_B1_aerobic'],43),
 ('recycle','内回流泵',10,(91,177,12),(87,182,7),(83.2,184,-.6),(83.2,184,-1.3),['LIQUID_B1_aerobic'],46),
 ('distribution','二沉配水井 · 污泥回流泵',10,(115,110,17),(107,117,11),(100,124,0),(100,124,-.6),['LIQUID_DWA_'],43),
 ('secondary','二沉池',24,(66,45,34),(48,58,25),(34,80,0),(34,80,-.8),['LIQUID_T1_'],42),
 ('contact','接触消毒池',18,(328,4,31),(307,10,23),(300,28.5,0),(297,28.5,-.5),['LIQUID_CT_'],42),
 ('meter','长喉计量渠 · 双渠',12,(351,17,17),(343,22,11),(338,29,.5),(338,29,.5),['LIQUID_METER','FILM_WaterMeter'],46),
 ('outfall','出水口',18,(494,10,3),(487,20,-1),(477,29,-6.3),(477,29,-6.5),['FILM_WaterOutfall'],43),
 ('ending','净水归河',10,(545,-30,100),(690,-170,310),(450,45,-3),(300,110,0),[],38),
]
ROWS=[(key,title,seconds,*[(100-p[0],326-p[1],p[2]) for p in (p0,p1,t0,t1)],water,lens) if key in ('anaerobic','anoxic','aerobic','recycle') else (key,title,seconds,p0,p1,t0,t1,water,lens) for key,title,seconds,p0,p1,t0,t1,water,lens in ROWS]
shots=[];start=1
for key,title,seconds,p0,p1,t0,t1,water,lens in ROWS:
 end=start+seconds*24-1
 shots.append(dict(id=key,title=title,seconds=seconds,start=start,end=end,camera_start=p0,camera_end=p1,target_start=t0,target_end=t1,water=water,lens=lens,reveal_start=round(start+(end-start)*.42),dry_start=round(start+(end-start)*.50),dry_end=round(start+(end-start)*.79),restore_end=round(start+(end-start)*.88)))
 start=end+1
assert start-1 == 6480
cfg=dict(fps=24,frames=6480,duration_seconds=270,resolution=[3840,2160],samples=192,noise_threshold=.015,shots=shots,
 assumptions=['Presentation geometry, not hydraulic simulation or selected manufacturer internals.','Pump and blower cross-sections are generic explanatory additions.','All six blower/pump rotors animate for mechanism demonstration; design remains four duty plus two standby.','Primary and secondary scraper motion is accelerated; rotating impellers slowed for readability.'],
 geometry=dict(pump_rotor_radius_fraction=.32,blower_rotor_radius=.48,blower_internal_offset=[0,-.35,1.35],outfall_start=[476.85,29,-6.85],outfall_end=[482.3,29,-8.13]),
 speeds=dict(secondary_period_seconds=100,primary_period_seconds=80,pump_demo_rps=.8,blower_demo_rps=.7))
(ROOT/'data/film.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
parser=argparse.ArgumentParser();parser.add_argument('--font',type=Path);args=parser.parse_args()
font_path=args.font or Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc'
if not font_path.exists():raise RuntimeError('To regenerate captions, pass --font with an installed CJK font; existing PNG captions need no font installation.')
titlefont=ImageFont.truetype(str(font_path),76);small=ImageFont.truetype(str(font_path),34)
for index,shot in enumerate(shots,1):
 for mode in ['wet','dry']:
  # Compact bottom-left overlay, rendered at final 4K resolution.
  im=Image.new('RGBA',(1800,280));d=ImageDraw.Draw(im)
  d.rounded_rectangle((0,0,1760,260),radius=12,fill=(8,19,25,178))
  d.rectangle((34,40,41,216),fill=(80,195,188,255))
  d.text((74,31),f'{index:02d}  /  {len(shots):02d}',font=small,fill=(166,198,199,255))
  d.text((72,83),shot['title'],font=titlefont,fill=(246,248,248,255))
  note=''
  if mode=='dry' and shot['water']:note='隐藏水体 · 机构展示'
  if shot['id'] in ('primary','secondary'):note+=('  ·  ' if note else '')+'机械动作加速展示'
  if shot['id']=='blowers':note='内部机构示意 · 慢速展示' if mode=='dry' else '供气系统'
  if shot['id'] in ('pumps','recycle','distribution') and mode=='dry':note+=' · 叶轮示意'
  if shot['id']=='ending':note='Blower: APG-Neuros NX300 / a1call / CC BY 4.0 · modified'
  if note:d.text((76,198),note,font=small,fill=(198,213,216,255))
  im.save(OUT/f'{shot["id"]}_{mode}.png')
print('Prepared 17 shots, 6480 frames, 270 seconds and 34 caption overlays.')
