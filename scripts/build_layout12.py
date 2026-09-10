"""第12项教师审阅后平面复核。

坐标单位m，西南角为原点，x向东/y向北。生成SVG、构筑物坐标、
外部管线平面长度及面积校核。净尺寸、结构外缘和占地包络分开表达。
"""
import csv
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "计算成果" / "第12项附件"
OUT.mkdir(parents=True, exist_ok=True)

# id, label, xmin, ymin, width, height, category, status
units = [
    ("G1", "粗格栅", 348, 284, 24, 8, "water", "两格并联运行，单格可短时承担检修流量"),
    ("P", "提升泵站", 348, 258, 24, 20, "water", "4泵3用1备；含湿井及检修包络"),
    ("G2", "细格栅", 304, 260, 24, 12, "water", "两格并联运行，非一用一备"),
    ("SA", "沉砂A", 212, 266, 32, 7, "water", "30×3.3净尺寸外包"),
    ("SB", "沉砂B", 260, 266, 32, 7, "water", "30×3.3净尺寸外包"),
    ("DIS", "消毒计量", 350, 25, 22, 30, "reserve", "课程阶段占地预留，非定型池容"),
    ("CHEM", "碳源/除磷加药", 350, 110, 22, 20, "reserve", "含储罐、计量及卸料安全复核预留"),
    ("AIR", "鼓风机房", 180, 110, 40, 18, "reserve", "6台，5用1备；吊装由厂家复核"),
    ("DWA", "二沉配水A", 112, 106, 16, 10, "water", "A线3池配水井占地包络"),
    ("DWB", "二沉配水B", 272, 106, 16, 10, "water", "B线3池配水井占地包络"),
    ("ADMIN", "管理及生活预留", 270, 30, 75, 20, "reserve", "只预留用地，不设计建筑"),
    ("SL", "污泥转运接口", 35, 210, 25, 35, "reserve", "非完整污泥处理线"),
    ("MAINT", "维修配电预留", 35, 110, 20, 20, "reserve", "功能及安全间距另核"),
    ("FUT", "连续发展用地", 40, 260, 120, 25, "future", "不代表可扩建同等处理规模"),
]

# Four D31 primary tanks.  A 0.40 m structural wall gives D31.8 outer edge;
# the 34 m square package includes about 1.1 m operating strip each side.
primary_centres = [80, 160, 240, 320]
for i, x in enumerate(primary_centres, 1):
    units.extend([
        (f"C{i}", f"初沉{i}", x - 17, 208, 34, 34, "water", "净D31；结构外径D31.8；D34为含操作带包络"),
        (f"B{i}", f"A²/O {i}", x - 24.5, 135, 49, 58, "water", "净54×45×5；旋转后含操作带包络49×58"),
    ])

# Six D36 secondary tanks, three per water line.  D36.8 is the structural outer
# diameter for a preliminary 0.40 m wall; D40 is an occupancy envelope, not wall.
secondary_centres = [45, 105, 165, 235, 295, 355]
for i, x in enumerate(secondary_centres, 1):
    units.append((f"T{i}", f"二沉{i}", x - 20, 55, 40, 40, "water", "净D36；结构外径D36.8；D40为含操作带包络"))

# 6 m roads; intersections are counted once.
roads = [(17, 17, 6, 283), (377, 17, 6, 236), (17, 17, 383, 6), (17, 247, 366, 6), (17, 197, 366, 6)]


def intersects(a, b):
    return max(a[0], b[0]) < min(a[0] + a[2], b[0] + b[2]) and max(a[1], b[1]) < min(a[1] + a[3], b[1] + b[3])


def union_area(rects):
    xs = sorted({v for x, y, w, h in rects for v in (x, x + w)})
    ys = sorted({v for x, y, w, h in rects for v in (y, y + h)})
    return sum((b - a) * (d - c) for a, b in zip(xs, xs[1:]) for c, d in zip(ys, ys[1:]) if any(x <= (a + b) / 2 <= x + w and y <= (c + d) / 2 <= y + h for x, y, w, h in rects))


for i, unit in enumerate(units):
    area = unit[2:6]
    assert area[0] >= 0 and area[1] >= 0
    assert area[0] + area[2] <= 400 and area[1] + area[3] <= 300, unit[0]
    for other in units[i + 1:]:
        assert not intersects(area, other[2:6]), (unit[0], other[0])
    for road in roads:
        assert not intersects(area, road), (unit[0], "road")

routes = []


def route(name, kind, points, note):
    length = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
    assert all(0 <= x <= 400 and 0 <= y <= 300 for x, y in points)
    routes.append((name, kind, points, length, note))


route("进厂至粗栅", "water", [(360, 300), (360, 292)], "厂界到单元包络接口")
route("粗栅至泵站", "water", [(360, 284), (360, 278)], "单元间净平面长度")
route("泵站至细栅", "water", [(348, 268), (348, 266), (328, 266)], "不含单泵4+7+1 m内部支管")
route("细栅至分流点", "water", [(304, 266), (300, 266), (300, 280)], "概念分流节点")
route("分流至沉砂A", "water", [(300, 280), (244, 280), (244, 269.5)], "A线")
route("分流至沉砂B", "water", [(300, 280), (292, 280), (292, 269.5)], "B线")
route("沉砂A至初沉分配", "water", [(212, 269.5), (212, 250), (120, 250)], "沿北侧道路地下敷设")
route("沉砂B至初沉分配", "water", [(260, 269.5), (260, 250), (280, 250)], "沿北侧道路地下敷设")

for i, x in enumerate(primary_centres, 1):
    header = 120 if i <= 2 else 280
    route(f"初沉分配至C{i}", "water", [(header, 250), (x, 250), (x, 242)], "至D34占地包络，不含池内中心管")
    route(f"C{i}至B{i}", "water", [(x, 208), (x, 193)], "单体外缘间净长")
    dwx = 120 if i <= 2 else 280
    route(f"B{i}至二沉配水", "water", [(x, 135), (x, 125), (dwx, 125), (dwx, 116)], "两座生物池汇入本线配水井")

for i, x in enumerate(secondary_centres, 1):
    dwx = 120 if i <= 3 else 280
    route(f"二沉配水至T{i}", "water", [(dwx, 106), (dwx, 102), (x, 102), (x, 95)], "至D40包络；中心进水竖管另计20 m")
    route(f"T{i}至消毒", "water", [(x, 55), (x, 50), (350, 50), (350, 55)], "含本线共用出水走廊；单路径不可相加作工程量")
    corridor = 120 if i <= 3 else 280
    target_bio = [80, 80, 160, 240, 320, 320][i - 1]
    route(f"RAS{i}", "ras", [(x, 95), (x, 102), (corridor, 102), (corridor, 125), (target_bio, 125), (target_bio, 135)], "按中心至包络20 m另计；路径用于最不利支干管复核")

for i, x in enumerate(primary_centres, 1):
    route(f"AIR至B{i}", "air", [(200, 128), (200, 130), (x, 130), (x, 135)], "共用空气干线；不含池内支管")
route("消毒至出厂", "water", [(372, 40), (400, 40)], "只到东厂界，厂外实测长度待定")

water_area = sum(u[4] * u[5] for u in units if u[6] == "water")
reserve_area = sum(u[4] * u[5] for u in units if u[6] == "reserve")
future_area = sum(u[4] * u[5] for u in units if u[6] == "future")
road_area = union_area(roads)
remaining = 120000 - water_area - reserve_area - future_area - road_area
green_target = 36000
other_available = remaining - green_target
assert other_available > 0

summary = {
    "site_m2": 120000,
    "water_envelopes_m2": water_area,
    "auxiliary_reserve_m2": reserve_area,
    "future_m2": future_area,
    "road_union_m2": road_area,
    "unallocated_m2": remaining,
    "provisional_green_target_m2": green_target,
    "other_available_m2": other_available,
    "primary_count": 4,
    "primary_net_diameter_m": 31,
    "secondary_count": 6,
    "secondary_net_diameter_m": 36,
    "secondary_net_area_m2": 6 * math.pi * 36**2 / 4,
    "secondary_peak_surface_load_m3_m2_h": 5850 / (6 * math.pi * 36**2 / 4),
    "checks": "all packages within boundary; no package overlap; no road overlap; area closes to 120000 m2",
}

lengths = {name: length for name, kind, points, length, note in routes}
common = sum(lengths[n] for n in ["进厂至粗栅", "粗栅至泵站", "泵站至细栅", "细栅至分流点", "消毒至出厂"])
summary["external_water_path_lengths_m"] = {}
for i in range(1, 5):
    line = "A" if i <= 2 else "B"
    tank = (1, 3, 4, 6)[i - 1]
    names = [f"分流至沉砂{line}", f"沉砂{line}至初沉分配", f"初沉分配至C{i}", f"C{i}至B{i}", f"B{i}至二沉配水", f"二沉配水至T{tank}", f"T{tank}至消毒"]
    summary["external_water_path_lengths_m"][str(i)] = common + sum(lengths[n] for n in names)

assert water_area + reserve_area + future_area + road_area + green_target + other_available == 120000

with (OUT / "构筑物坐标.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["编号", "名称", "西边x_m", "南边y_m", "东西宽_m", "南北长_m", "类别", "依据状态"])
    writer.writerows(units)
with (OUT / "管线平面长度.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["管段", "类型", "折点坐标_m", "平面长度_m", "说明"])
    for name, kind, points, length, note in routes:
        writer.writerow([name, kind, json.dumps(points), round(length, 2), note])
with (OUT / "面积校核.json").open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")


def rect(x, y, width, height, fill, stroke="#889", dash=""):
    return f'<rect x="{25+x}" y="{335-y-height}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" stroke-width="0.45" stroke-dasharray="{dash}"/>'


svg = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1440" viewBox="0 0 480 480">',
    '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#147aab"/></marker></defs>',
    '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#20333c;font-size:3.5px}.small{font-size:3px}</style>',
    '<rect width="480" height="480" fill="#fff"/>',
    '<text x="25" y="12" style="font-size:7px">第12项：教师审阅后总平面复核 · 400 m × 300 m</text>',
    '<text x="25" y="21">两条水线、4系列A²/O、4座D31初沉、6座D36二沉；北向为本次坐标约定。</text>',
    rect(0, 0, 400, 300, "#f0f5e9", "#1c3932"),
]
for road in roads:
    svg.append(rect(*road, "#d9dfe1", "#d9dfe1"))
for name, label, x, y, width, height, kind, status in units:
    fill = {"water": "#d8edf6", "reserve": "#fff0d1", "future": "#e5e0f4"}[kind]
    svg.append(rect(x, y, width, height, fill, "#4b6873", "2 1" if kind != "water" else ""))
    if (name.startswith("C") or name.startswith("T")) and name[1:].isdigit():
        structural_diameter = 31.8 if name.startswith("C") else 36.8
        svg.append(f'<circle cx="{25+x+width/2}" cy="{335-y-height/2}" r="{structural_diameter/2}" fill="none" stroke="#58788a" stroke-width=".6"/>')
    shown = name if width < 35 else f"{name} {label}"
    svg.append(f'<text x="{25+x+width/2}" y="{335-y-height/2-1}" text-anchor="middle">{escape(shown)}</text>')
    if height >= 10:
        svg.append(f'<text class="small" x="{25+x+width/2}" y="{335-y-height/2+4}" text-anchor="middle">{width:g} × {height:g} m</text>')
for name, kind, points, length, note in routes:
    if kind != "water":
        continue
    polyline = " ".join(f"{25+x},{335-y}" for x, y in points)
    svg.append(f'<polyline points="{polyline}" fill="none" stroke="#147aab" stroke-width=".5" marker-end="url(#arrow)"/>')
svg.extend([
    '<text x="380" y="31">进水 (360,300)</text>',
    '<path d="M445 55 L445 34" stroke="#243e43" stroke-width="1" marker-end="url(#arrow)"/><text x="443" y="29">N</text>',
    '<path d="M447 125 Q433 210 444 290" fill="none" stroke="#39aaca" stroke-width="2"/><text x="444" y="205">河道</text>',
    '<text x="25" y="345">西南角(0,0)。圆线为结构外缘；方框为含操作带的占地包络，不能把包络差值当池壁厚。</text>',
    '<text x="25" y="354">主流程蓝线；RAS和空气路线见CSV。池内中心管、竖向、阀件及施工转弯半径未计入平面长度。</text>',
    '<text x="25" y="363">灰：6m道路；蓝：水处理单元；橙：辅助预留；紫：连续发展用地；浅绿：其余用地。</text>',
    '<path d="M350 376 h50 M350 374 v4 M375 374 v4 M400 374 v4" stroke="#263c44" fill="none"/><text x="345" y="382">0</text><text x="372" y="382">25</text><text x="397" y="382">50 m</text>',
    '<text x="25" y="400">格栅：G1/G2均为两格正常并联；泵站：4台3用1备。DWA/DWB分别向3座二沉池配水。</text>',
    '<text x="25" y="410">初沉：净D31、结构外径D31.8、占地包络D34；二沉：净D36、结构外径D36.8、占地包络D40。</text>',
    f'<text x="25" y="432">占地：水线包络 {water_area:g} m² + 辅助预留 {reserve_area:g} m² + 道路并集 {road_area:g} m²</text>',
    f'<text x="25" y="442">发展用地 {future_area:g} m²；未分配 {remaining:g} m²，其中规划绿地目标 {green_target:g} m²。</text>',
    '<text x="25" y="462">课程阶段复核图；正式提交前仍应以CAD/BIM补齐管廊标高、检修吊装、消防、除臭和结构条件。</text>',
    '</svg>',
])
with (OUT / "平面初校.svg").open("w", encoding="utf-8", newline="\n") as handle:
    handle.write("\n".join(svg))
print(json.dumps(summary, ensure_ascii=False, indent=2))
