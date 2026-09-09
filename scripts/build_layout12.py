"""第12项平面初校。标准库运行；坐标单位m，西南原点，x向东/y向北。
生成SVG、坐标/管线CSV及面积校核JSON；二沉和附属设施均为占地预留。
"""
import csv
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '计算成果' / '第12项附件'
OUT.mkdir(parents=True, exist_ok=True)
# id, label, xmin, ymin, width, height, category, status
units = [
    ('G1', '粗格栅', 348, 284, 24, 8, 'water', '槽群及操作带预留'),
    ('P', '提升泵站', 348, 258, 24, 20, 'water', '含16×10集水池及检修预留'),
    ('G2', '细格栅', 304, 260, 24, 12, 'water', '槽群及操作带预留'),
    ('SA', '沉砂A', 212, 266, 32, 7, 'water', '30×3.3净尺寸外包预留'),
    ('SB', '沉砂B', 260, 266, 32, 7, 'water', '30×3.3净尺寸外包预留'),
    ('DIS', '消毒计量', 350, 65, 22, 30, 'reserve', '完善项占地预留，非定型池容'),
    ('CHEM', '加药区', 350, 110, 22, 20, 'reserve', '补碳补碱及除磷药剂预留'),
    ('AIR', '鼓风机房', 180, 110, 40, 18, 'reserve', '6台设备布置/吊装待厂家复核'),
    ('ADMIN', '管理及生活预留', 290, 30, 75, 20, 'reserve', '仅预留用地，不设计建筑'),
    ('SL', '污泥转运接口', 35, 210, 25, 35, 'reserve', '非完整污泥处理线'),
    ('MAINT', '维修配电预留', 35, 110, 20, 20, 'reserve', '功能及安全间距另核'),
    ('FUT', '连续发展用地', 40, 260, 120, 25, 'future', '不代表可扩建同等处理规模'),
]
centers = [80, 160, 240, 320]
for i, x in enumerate(centers, 1):
    units.extend([
        (f'C{i}', f'初沉{i}', x-15, 210, 30, 30, 'water', 'D28外包D30，用方形包络计地'),
        (f'B{i}', f'A²/O {i}', x-24.5, 135, 49, 58, 'water', '净45×54旋转后外包49×58'),
        (f'T{i}', f'二沉预留{i}', x-23, 57, 46, 46, 'reserve', '暂按净D44外包D46，未完成第10项'),
    ])
# 道路矩形的并集计面积，不重复计交叉口；宽6m为本项假定。
roads = [(17,17,6,283),(377,17,6,236),(17,17,383,6),
         (17,247,366,6),(17,197,366,6),(117,17,6,236),(277,17,6,236)]
def intersects(a,b):
    return max(a[0],b[0]) < min(a[0]+a[2],b[0]+b[2]) and max(a[1],b[1]) < min(a[1]+a[3],b[1]+b[3])
def union_area(rects):
    xs=sorted({v for x,y,w,h in rects for v in [x,x+w]})
    ys=sorted({v for x,y,w,h in rects for v in [y,y+h]})
    return sum((b-a)*(d-c) for a,b in zip(xs,xs[1:]) for c,d in zip(ys,ys[1:])
               if any(x <= (a+b)/2 <= x+w and y <= (c+d)/2 <= y+h for x,y,w,h in rects))
for i,u in enumerate(units):
    a=u[2:6]
    assert a[0]>=0 and a[1]>=0 and a[0]+a[2]<=400 and a[1]+a[3]<=300,u[0]
    for v in units[i+1:]: assert not intersects(a,v[2:6]),(u[0],v[0])
    for r in roads: assert not intersects(a,r),(u[0],'road')
routes=[]
def route(name, kind, pts, note):
    length=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))
    assert all(0<=x<=400 and 0<=y<=300 for x,y in pts)
    routes.append((name,kind,pts,length,note))
route('进厂至粗栅','water',[(360,300),(360,292)],'厂界到单元外包接口')
route('粗栅至泵站','water',[(360,284),(360,278)],'单元间净平面长度')
route('泵站至细栅','water',[(348,268),(348,266),(328,266)],'泵站内部管道及竖向长度另计')
route('细栅至分流点','water',[(304,266),(300,266),(300,280)],'分流点为概念节点，配水井未定型')
route('分流至沉砂A','water',[(300,280),(244,280),(244,269.5)],'A线')
route('分流至沉砂B','water',[(300,280),(292,280),(292,269.5)],'B线')
route('沉砂A至初沉分配','water',[(212,269.5),(212,250),(120,250)],'配水干线沿北侧道路地下敷设')
route('沉砂B至初沉分配','water',[(260,269.5),(260,250),(280,250)],'配水干线沿北侧道路地下敷设')
for i,x in enumerate(centers,1):
    header=120 if i<=2 else 280
    route(f'初沉分配至C{i}','water',[(header,250),(x,250),(x,240)],'不包含池内进水设施')
    route(f'C{i}至B{i}','water',[(x,210),(x,193)],'穿路段埋深及交叉由第11/13项核定')
    route(f'B{i}至T{i}','water',[(x,135),(x,103)],'二沉北侧外包边界，池内中心进水另计')
    route(f'T{i}至消毒','water',[(x,57),(x,53),(350,53),(350,80)],'含共用出水干线；不得将四条长度相加作为唯一管长')
    side = -1 if i == 2 else 1
    corridor = {1:110, 2:130, 3:270, 4:348}[i]
    route(f'RAS{i}','ras',[(x+side*23,80),(corridor,80),(corridor,205),(x,205),(x,193)],'二沉外包接口至厌氧入口；避开鼓风机房，泵/阀/竖向另计')
    route(f'AIR至B{i}','air',[(200,128),(200,130),(x,130),(x,135)],'含共用空气干线；管件/竖向/池内支管另计')
route('消毒至出厂','water',[(372,80),(400,80)],'仅到厂界，厂界到河道未测不能估为零')
water_area=sum(u[4]*u[5] for u in units if u[6]=='water')
reserve_area=sum(u[4]*u[5] for u in units if u[6]=='reserve')
future_area=sum(u[4]*u[5] for u in units if u[6]=='future')
road_area=union_area(roads)
remaining=120000-water_area-reserve_area-future_area-road_area
green_target=36000  # 30%仅为本次规划分配目标，并非引用法规最低值
extra=remaining-green_target
assert extra>0
summary=dict(site_m2=120000,water_envelopes_m2=water_area,
             auxiliary_and_secondary_reserve_m2=reserve_area,future_m2=future_area,
             road_union_m2=road_area,unallocated_m2=remaining,
             provisional_green_target_m2=green_target,other_available_m2=extra,
             secondary_screen_area_m2=4*math.pi*44**2/4,
             secondary_peak_surface_load=5850/(4*math.pi*44**2/4),
             checks='包络不重叠；不压道路；均在厂界内；占地分项相加等于120000m²')
lengths={n:l for n,k,p,l,note in routes}
common=sum(lengths[n] for n in ['进厂至粗栅','粗栅至泵站','泵站至细栅','细栅至分流点','消毒至出厂'])
summary['external_water_path_lengths_m']={}
for i in range(1,5):
    line='A' if i<=2 else 'B'
    names=[f'分流至沉砂{line}',f'沉砂{line}至初沉分配',f'初沉分配至C{i}',f'C{i}至B{i}',f'B{i}至T{i}',f'T{i}至消毒']
    summary['external_water_path_lengths_m'][str(i)]=common+sum(lengths[n] for n in names)
assert water_area+reserve_area+future_area+road_area+green_target+extra==120000
with (OUT/'构筑物坐标.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['编号','名称','西边x_m','南边y_m','东西宽_m','南北长_m','类别','依据状态']);w.writerows(units)
with (OUT/'管线平面长度.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['管段','类型','折点坐标_m','平面长度_m','说明'])
    for n,k,p,l,note in routes:w.writerow([n,k,json.dumps(p),round(l,2),note])
(OUT/'面积校核.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# SVG是坐标数据的图示；蓝色外包为已有单体的占地预留，橙色为未定型设施。
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1440" viewBox="0 0 480 480">',
'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#147aab"/></marker></defs>',
'<style>text{font-family:Arial,"PingFang SC","Microsoft YaHei",sans-serif;fill:#20333c;font-size:3.5px}.small{font-size:3px}</style>',
'<rect width="480" height="480" fill="#fff"/><text x="25" y="12" style="font-size:7px">第12项：污水厂平面初校 · 400 m × 300 m</text>',
'<text x="25" y="21">两条水线各2系列；全部尺寸为平面占地包络，非施工图。北向为本次布置约定。</text>']
def rect(x,y,w,h,fill,stroke='#889',dash=''):
    return f'<rect x="{25+x}" y="{335-y-h}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="0.45" stroke-dasharray="{dash}"/>'
svg.append(rect(0,0,400,300,'#f0f5e9','#1c3932'))
for x,y,w,h in roads:svg.append(rect(x,y,w,h,'#d9dfe1','#d9dfe1'))
for n,label,x,y,w,h,k,status in units:
    fill={'water':'#d8edf6','reserve':'#fff0d1','future':'#e5e0f4'}[k]
    svg.append(rect(x,y,w,h,fill,'#4b6873','2 1' if k!='water' else ''))
    if n.startswith('C') and n[1:].isdigit() or n.startswith('T') and n[1:].isdigit():
        svg.append(f'<circle cx="{25+x+w/2}" cy="{335-y-h/2}" r="{w/2}" fill="none" stroke="#58788a" stroke-width=".5"/>')
    shown=n if w<35 else n+' '+label
    svg.append(f'<text x="{25+x+w/2}" y="{335-y-h/2-1}" text-anchor="middle">{escape(shown)}</text>')
    if h>=10:svg.append(f'<text class="small" x="{25+x+w/2}" y="{335-y-h/2+4}" text-anchor="middle">{w:g} × {h:g} m</text>')
for n,k,pts,l,note in routes:
    if k!='water':continue  # 回流和空气单独在CSV列出，避免叠线遮蔽平面
    s=' '.join(f'{25+x},{335-y}' for x,y in pts)
    svg.append(f'<polyline points="{s}" fill="none" stroke="#147aab" stroke-width=".55" marker-end="url(#arrow)"/>')
svg.extend(['<text x="380" y="31">进水 (360,300)</text>',
'<text x="8" y="39" transform="rotate(-90 8 39)">物流门</text>',
'<text x="425" y="318">管理门</text>',
'<path d="M445 55 L445 34" stroke="#243e43" stroke-width="1" marker-end="url(#arrow)"/><text x="443" y="29">N</text>',
'<path d="M453 320 L432 298" stroke="#789" stroke-width=".8" marker-end="url(#arrow)"/><text x="430" y="326">夏季东南风</text>',
'<path d="M447 125 Q433 210 444 290" fill="none" stroke="#39aaca" stroke-width="2"/><text x="444" y="205">河道</text>',
'<text x="430" y="214" class="small">位置示意</text>',
'<text x="25" y="345">西南角(0,0)；x向东、y向北；坐标表/管线长度表另附。二沉D44仅为占地筛查假定。</text>',
'<text x="25" y="353">灰：6m道路预留；蓝：已算单体的外包；橙：二沉及辅助预留；紫：发展用地；浅绿：未分配用地。</text>',
'<text x="25" y="361">主流程蓝线；RAS/空气概念路径见CSV。穿路管线按地下敷设预留，标高及交叉尚未校核。</text>',
'<text x="25" y="369">环路转弯、消防、绿化详图、除臭及施工吊装条件待专项复核。图中未分配用地不等于实际绿地。</text>',
'<path d="M350 376 h50 M350 374 v4 M375 374 v4 M400 374 v4" stroke="#263c44" fill="none"/><text x="345" y="382">0</text><text x="372" y="382">25</text><text x="397" y="382">50 m</text>',
'<text x="25" y="398">编号：G1 粗格栅 · P 提升泵站 · G2 细格栅 · SA/SB 曝气沉砂 · C1–C4 初沉池</text>',
'<text x="25" y="408">B1–B4 生物池 · T1–T4 二沉预留 · DIS 消毒计量 · CHEM 加药 · AIR 鼓风机房</text>',
'<text x="25" y="418">SL 污泥转运接口 · MAINT 维修配电预留 · ADMIN 管理生活预留 · FUT 发展用地</text>',
f'<text x="25" y="438">占地：水线包络 {water_area:g} m² + 二沉及附属预留 {reserve_area:g} m² + 道路并集 {road_area:g} m²</text>',
f'<text x="25" y="448">另留发展用地 {future_area:g} m²；未分配 {remaining:g} m²（包含拟分配绿地，非全部真实绿地）。</text>',
'<text x="25" y="462">本图仅用于第12项几何与占地初校；第10、11项未完成，出水标高与最终池数仍待闭合。</text></svg>'])
(OUT/'平面初校.svg').write_text('\n'.join(svg),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
