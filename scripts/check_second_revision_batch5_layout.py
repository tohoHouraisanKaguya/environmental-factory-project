#!/usr/bin/env python3
"""Generate and verify the second-revision batch-5 site layout deliverables.

Coordinates use metres. The south-west site corner is (0, 0), x points east,
and y points north. Occupancy envelopes are for course-layout checking only;
they are deliberately kept separate from process net and structural sizes.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUT = (
    ROOT
    / "第二次修改协作项目_2026-09-13"
    / "02_成果回收"
    / "第07组_总平面坐标与管线"
)
SITE_WIDTH = 400.0
SITE_HEIGHT = 300.0


def unit(
    code: str,
    name: str,
    x: float,
    y: float,
    width: float,
    height: float,
    category: str,
    net_size: str,
    structural_size: str,
    note: str,
    shape: str = "rect",
) -> dict:
    return {
        "code": code,
        "name": name,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "cx": x + width / 2,
        "cy": y + height / 2,
        "category": category,
        "net_size": net_size,
        "structural_size": structural_size,
        "note": note,
        "shape": shape,
    }


UNITS = [
    unit("G1", "粗格栅", 348, 278, 24, 8, "water", "2格", "待结构深化", "两格正常并联"),
    unit("P", "进水井/提升泵站", 348, 250, 24, 24, "water", "2×(16×10×1.2 m调节段)", "待结构深化", "每线2用1备"),
    unit("G2", "细格栅", 310, 254, 28, 14, "water", "2格", "待结构深化", "两格正常并联"),
    unit("SA", "曝气沉砂池A", 190, 270, 34, 8, "water", "30×3.8×2.55 m", "约30.8×4.6 m", "含两侧操作带"),
    unit("SB", "曝气沉砂池B", 240, 270, 34, 8, "water", "30×3.8×2.55 m", "约30.8×4.6 m", "含两侧操作带"),
    unit("PDA", "初沉配水井A", 95, 254, 10, 10, "water", "课程暂定6×4 m", "待结构深化", "向C1、C2等量配水"),
    unit("PDB", "初沉配水井B", 295, 254, 10, 10, "water", "课程暂定6×4 m", "待结构深化", "向C3、C4等量配水"),
    unit("DWA", "二沉配水井A", 91, 118, 18, 12, "water", "暂按16×10 m", "待结构深化", "接B1、B2，服务T1—T4"),
    unit("DWB", "二沉配水井B", 291, 118, 18, 12, "water", "暂按16×10 m", "待结构深化", "接B3、B4，服务T5—T8"),
    unit("AIR", "鼓风机房", 176, 116, 48, 18, "auxiliary", "6台AT400级机组", "待厂家确认", "含吊装和进气预留"),
    unit("CHEM", "碳源/除磷加药间", 330, 116, 42, 18, "auxiliary", "甲醇、FeCl3设备预留", "待专项深化", "与二沉前投加接口相连"),
    unit("ADMIN", "管理/化验预留", 30, 18, 76, 22, "management", "功能合并预留", "待建筑设计", "按交通和功能分区暂定"),
    unit("MAINT", "维修/配电预留", 116, 18, 44, 22, "auxiliary", "功能合并预留", "待建筑设计", "靠近南侧主入口"),
    unit("NAOCL", "次氯酸钠储存加药", 232, 18, 34, 22, "auxiliary", "2×约50 m3工作容积", "待安全专项深化", "低温、避光、库存不超过7 d"),
    unit("CT", "折流接触池", 274, 17, 50, 23, "water", "2×(45×8×4.8 m)", "约45.8×18.4 m", "8 m为单格净水宽；包络含操作带"),
    unit("METER", "计量/控制井", 330, 18, 16, 22, "water", "2条1.50 m长喉道", "待设备深化", "位于接触池之后"),
    unit("FUT", "连续发展用地", 20, 266, 140, 20, "future", "2800 m2连续用地", "不适用", "仅表明发展方向，不代表同规模扩建能力"),
]


# Four horizontal-flow primary clarifiers: process net 58 x 14.5 m;
# 63 x 20 m is an occupancy envelope, not a structural size.
PRIMARY_CENTRES = [50.0, 150.0, 250.0, 350.0]
for index, centre_x in enumerate(PRIMARY_CENTRES, 1):
    UNITS.append(
        unit(
            f"C{index}",
            f"平流初沉池{index}",
            centre_x - 31.5,
            216,
            63,
            20,
            "water",
            "58×14.5×3.5 m",
            "约58.8×15.3 m",
            "包络含约2 m/侧操作带",
        )
    )


# Four A2/O series: process net 70 x 45 x 5 m; 75 x 50 m occupancy envelope.
A2O_CENTRES = PRIMARY_CENTRES
for index, centre_x in enumerate(A2O_CENTRES, 1):
    UNITS.append(
        unit(
            f"B{index}",
            f"A2/O系列{index}",
            centre_x - 37.5,
            138,
            75,
            50,
            "water",
            "70×45×5 m",
            "约70.8×45.8 m",
            "包络含约2 m/侧操作带",
        )
    )


# Eight D37 secondary clarifiers. D37.8 is a preliminary structural edge;
# D42 is the occupancy envelope including about 2.1 m operating band per side.
SECONDARY_CENTRES = [34.0, 78.0, 122.0, 166.0, 234.0, 278.0, 322.0, 366.0]
for index, centre_x in enumerate(SECONDARY_CENTRES, 1):
    UNITS.append(
        unit(
            f"T{index}",
            f"辐流二沉池{index}",
            centre_x - 21,
            59,
            42,
            42,
            "water",
            "净D37 m，中心井D6 m",
            "暂按D37.8 m",
            "D42为含操作带方包络",
            shape="circle",
        )
    )


# Main roads are 6 m; the southern process access lane is 4 m. These are
# course-layout adopted widths and do not replace a fire-engineering review.
ROADS = [
    {"code": "R-W", "x": 6, "y": 6, "width": 6, "height": 288, "kind": "main"},
    {"code": "R-E", "x": 388, "y": 6, "width": 6, "height": 288, "kind": "main"},
    {"code": "R-N", "x": 12, "y": 288, "width": 376, "height": 6, "kind": "main"},
    {"code": "R-S", "x": 12, "y": 6, "width": 376, "height": 6, "kind": "main"},
    {"code": "R-1", "x": 12, "y": 108, "width": 376, "height": 6, "kind": "main"},
    {"code": "R-2", "x": 12, "y": 204, "width": 376, "height": 6, "kind": "main"},
    {"code": "R-3", "x": 12, "y": 242, "width": 376, "height": 6, "kind": "main"},
    {"code": "R-4", "x": 12, "y": 48, "width": 376, "height": 4, "kind": "secondary"},
]


def rect_intersects(a: dict, b: dict) -> bool:
    return (
        max(a["x"], b["x"]) < min(a["x"] + a["width"], b["x"] + b["width"])
        and max(a["y"], b["y"]) < min(a["y"] + a["height"], b["y"] + b["height"])
    )


def rectangle_union_area(rectangles: list[dict]) -> float:
    xs = sorted({value for r in rectangles for value in (r["x"], r["x"] + r["width"])})
    ys = sorted({value for r in rectangles for value in (r["y"], r["y"] + r["height"])})
    total = 0.0
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if any(r["x"] <= cx <= r["x"] + r["width"] and r["y"] <= cy <= r["y"] + r["height"] for r in rectangles):
                total += (x1 - x0) * (y1 - y0)
    return total


for i, current in enumerate(UNITS):
    assert current["x"] >= 0 and current["y"] >= 0
    assert current["x"] + current["width"] <= SITE_WIDTH
    assert current["y"] + current["height"] <= SITE_HEIGHT
    for other in UNITS[i + 1 :]:
        assert not rect_intersects(current, other), (current["code"], other["code"])
    for road in ROADS:
        assert not rect_intersects(current, road), (current["code"], road["code"])


ROUTES: list[dict] = []


def bend_count(points: list[tuple[float, float]], closed: bool = False) -> int:
    vectors = []
    for start, end in zip(points, points[1:]):
        vectors.append((math.copysign(1, end[0] - start[0]) if end[0] != start[0] else 0,
                        math.copysign(1, end[1] - start[1]) if end[1] != start[1] else 0))
    count = sum(a != b for a, b in zip(vectors, vectors[1:]))
    if closed and len(vectors) > 1 and vectors[-1] != vectors[0]:
        count += 1
    return count


def add_route(
    code: str,
    name: str,
    system: str,
    size: str,
    design_flow: str,
    points: list[tuple[float, float]],
    note: str,
    style: str = "solid",
) -> None:
    assert len(points) >= 2
    for x, y in points:
        assert 0 <= x <= SITE_WIDTH and 0 <= y <= SITE_HEIGHT, (code, x, y)
    for start, end in zip(points, points[1:]):
        assert start[0] == end[0] or start[1] == end[1], (code, start, end)
    length = sum(math.dist(start, end) for start, end in zip(points, points[1:]))
    ROUTES.append(
        {
            "code": code,
            "name": name,
            "system": system,
            "size": size,
            "design_flow": design_flow,
            "points": points,
            "length_m": length,
            "bends": bend_count(points, closed=points[0] == points[-1]),
            "note": note,
            "style": style,
        }
    )


# External wastewater line: unique physical segments, without in-tank travel.
add_route("W01", "进厂至粗格栅", "water", "题设D1200", "1.875 m3/s", [(360, 300), (360, 286)], "北界进水点距东界40 m")
add_route("W02", "粗格栅至提升泵站", "water", "双渠", "1.875 m3/s", [(360, 278), (360, 274)], "构筑物外缘间")
add_route("W03", "提升泵站至细格栅", "water", "2×DN1000", "0.9375 m3/s/线", [(348, 262), (343, 262), (343, 261), (338, 261)], "不含单泵内部DN700支管12 m")
add_route("W04", "细格栅至两线分流点", "water", "双渠", "1.875 m3/s", [(310, 261), (286, 261)], "维持两条并行处理线")
add_route("W05A", "分流点至沉砂池A", "water", "矩形渠", "0.9375 m3/s", [(286, 261), (286, 282), (224, 282), (224, 274)], "A水线")
add_route("W05B", "分流点至沉砂池B", "water", "矩形渠", "0.9375 m3/s", [(286, 261), (286, 282), (274, 282), (274, 274)], "B水线")
add_route("W06A", "沉砂池A至初沉配水井A", "water", "DN1200", "0.9375 m3/s", [(190, 274), (180, 274), (180, 264), (100, 264)], "避让连续发展用地")
add_route("W06B", "沉砂池B至初沉配水井B", "water", "DN1200", "0.9375 m3/s", [(240, 274), (240, 264), (300, 264)], "B水线")
for group, centre in (("A", 100), ("B", 300)):
    add_route(f"W07{group}F", f"初沉配水井{group}至分配干管", "water", "DN1200", "0.9375 m3/s", [(centre, 254), (centre, 250)], "井后短接")
for index, centre in enumerate(PRIMARY_CENTRES, 1):
    well_x = 100 if index <= 2 else 300
    add_route(f"W07C{index}", f"初沉分配至C{index}", "water", "DN900", "0.46875 m3/s", [(well_x, 250), (centre, 250), (centre, 236)], "井内等流设施后独立支管")
    add_route(f"W08C{index}", f"C{index}至B{index}", "water", "DN900", "0.46875 m3/s", [(centre, 216), (centre, 188)], "外缘间中心线")

for index, centre in enumerate(A2O_CENTRES, 1):
    well_x = 100 if index <= 2 else 300
    add_route(f"W09B{index}", f"B{index}至二沉配水井", "water", "DN1200", "0.820313 m3/s", [(centre, 138), (centre, 134), (well_x, 134), (well_x, 130)], "外部水量加RAS；内回流不进入本管")

secondary_branch_origins = [94, 98, 102, 106, 294, 298, 302, 306]
secondary_branch_levels = [104, 105, 106, 107, 104, 105, 106, 107]
for index, (centre, origin_x, corridor_y) in enumerate(zip(SECONDARY_CENTRES, secondary_branch_origins, secondary_branch_levels), 1):
    add_route(f"W10T{index}", f"配水井至T{index}中心", "water", "DN900", "0.410156 m3/s", [(origin_x, 118), (origin_x, corridor_y), (centre, corridor_y), (centre, 80)], "4个等高堰后各设独立支管；用相邻平行中心线表达，平面计至中心进水竖管")

# Secondary effluent: DN700 individual outlets join two DN1200 headers.
for index, centre in enumerate(SECONDARY_CENTRES[:4], 1):
    add_route(f"W11T{index}", f"T{index}出水支管", "water", "DN700", "0.234375 m3/s", [(centre, 59), (centre, 56)], "接A线出水汇流管")
for index, centre in enumerate(SECONDARY_CENTRES[4:], 5):
    add_route(f"W11T{index}", f"T{index}出水支管", "water", "DN700", "0.234375 m3/s", [(centre, 59), (centre, 54)], "接B线出水汇流管")
add_route("W11AH", "A线二沉出水汇流管", "water", "DN1200", "0.9375 m3/s", [(34, 56), (270, 56)], "T1—T4共用")
add_route("W11AC", "A线汇流管至接触池1格", "water", "DN1200", "0.9375 m3/s", [(270, 56), (270, 33), (274, 33)], "二沉澄清出水")
add_route("W11BH", "B线二沉出水汇流管", "water", "DN1200", "0.9375 m3/s", [(234, 54), (366, 54)], "T5—T8共用，在x=270处接出")
add_route("W11BC", "B线汇流管至接触池2格", "water", "DN1200", "0.9375 m3/s", [(270, 54), (270, 24), (274, 24)], "二沉澄清出水")
add_route("W12A", "接触池1格至计量渠1", "water", "1.50 m长喉道接口", "0.9375 m3/s", [(324, 33), (330, 33)], "计量位于消毒之后")
add_route("W12B", "接触池2格至计量渠2", "water", "1.50 m长喉道接口", "0.9375 m3/s", [(324, 24), (330, 24)], "计量位于消毒之后")
add_route("W13A", "计量渠1至出厂汇合点", "water", "渠道/连接管待定", "0.9375 m3/s", [(346, 33), (352, 33), (352, 29)], "计量后汇合")
add_route("W13B", "计量渠2至出厂汇合点", "water", "渠道/连接管待定", "0.9375 m3/s", [(346, 24), (352, 24), (352, 29)], "计量后汇合")
add_route("W14", "出厂汇合点至东厂界", "water", "DN1500", "1.875 m3/s", [(352, 29), (400, 29)], "仅计厂内；厂外至河道实测长度待定")

# Return activated sludge: each pool has a DN500 leg; each pair shares DN700.
for index, centre in enumerate(SECONDARY_CENTRES, 1):
    add_route(f"R{index}", f"T{index}回流污泥支管", "ras", "DN500", "0.175781 m3/s峰值", [(centre, 80), (centre, 116)], "接对应A2/O系列回流干管")
ras_pairs = [(1, 34, 78, 50), (2, 122, 166, 150), (3, 234, 278, 250), (4, 322, 366, 350)]
for series, x0, x1, target in ras_pairs:
    add_route(f"RH{series}", f"B{series}回流污泥干管", "ras", "DN700", "0.351563 m3/s峰值", [(x0, 116), (x1, 116)], "两座二沉池汇流")
    add_route(f"RB{series}", f"回流干管至B{series}", "ras", "DN700", "0.351563 m3/s峰值", [(target, 116), (target, 138)], "接厌氧段；设止回与隔离")

# Internal recycle is shown schematically inside each A2/O envelope.
for index, centre in enumerate(A2O_CENTRES, 1):
    add_route(f"IR{index}", f"B{index}混合液内回流", "internal", "DN1200", "1.171875 m3/s峰值", [(centre + 30, 143), (centre + 30, 183), (centre - 10, 183)], "池内平面暂计80 m；喷嘴与竖向由第08/09组复核", style="dash")

# Air ring and branches. The ring is a connected redundancy concept; vendor
# design must establish tapers, valves, condensate drains and actual pressure.
add_route("A00", "曝气环状母管", "air", "DN1200", "48000 Nm3/h工作量", [(10, 134), (390, 134), (390, 192), (10, 192), (10, 134)], "鼓风机房在(200,134)接入；道路下穿段设套管")
for index, centre in enumerate(A2O_CENTRES, 1):
    add_route(f"A{index}", f"至B{index}空气支管", "air", "DN700", "12000 Nm3/h", [(centre, 134), (centre, 138)], "接池内配气管")

# The assignment covers only the water line. Waste sludge and bypass are kept
# as explicit interfaces without pretending to design a full sludge process.
add_route("SLA", "A线剩余污泥至西侧边界", "sludge", "DN250接口", "运行排泥量待第08组", [(100, 116), (12, 116), (0, 116)], "仅到任务边界", style="dash")
add_route("SLB", "B线剩余污泥至西侧边界", "sludge", "DN250接口", "运行排泥量待第08组", [(300, 118), (12, 118), (0, 118)], "仅到任务边界", style="dash")
add_route("EM", "事故/检修超越预留", "bypass", "管径待专项核定", "不得作为常规排放", [(310, 261), (390, 261), (390, 29), (400, 29)], "沿东侧道路地下预留；启用须服从审批和运行规程", style="dash")


ROUTE_BY_CODE = {r["code"]: r for r in ROUTES}


def length(code: str) -> float:
    return ROUTE_BY_CODE[code]["length_m"]


# Hydraulic control paths repeat shared segments intentionally; they are not
# quantities. Eight routes map two secondary tanks to each A2/O series.
common_length = sum(length(code) for code in ("W01", "W02", "W03", "W04"))
PATHS = []
for tank in range(1, 9):
    series = (tank + 1) // 2
    line = "A" if tank <= 4 else "B"
    line_prefix = length(f"W05{line}") + length(f"W06{line}")
    primary_path = 4 + 50 + 14  # feed, half header, branch to the tank
    a2o_to_well = length(f"W09B{series}")
    tank_x = SECONDARY_CENTRES[tank - 1]
    well_to_tank = length(f"W10T{tank}")
    if line == "A":
        effluent_to_contact = 3 + (270 - tank_x) + 23 + 4
        terminal = length("W12A") + length("W13A") + length("W14")
    else:
        effluent_to_contact = 5 + abs(tank_x - 270) + 30 + 4
        terminal = length("W12B") + length("W13B") + length("W14")
    total = (
        common_length
        + line_prefix
        + primary_path
        + length(f"W08C{series}")
        + a2o_to_well
        + well_to_tank
        + effluent_to_contact
        + terminal
    )
    PATHS.append(
        {
            "path": f"进厂—C{series}—B{series}—T{tank}—接触池—计量—东厂界",
            "line": line,
            "series": series,
            "secondary": tank,
            "common_m": common_length,
            "pretreatment_to_primary_m": line_prefix + primary_path,
            "primary_to_a2o_m": length(f"W08C{series}"),
            "a2o_to_secondary_m": a2o_to_well + well_to_tank,
            "secondary_to_contact_m": effluent_to_contact,
            "contact_to_boundary_m": terminal,
            "external_centerline_total_m": total,
        }
    )


WORST_WATER_PATH = max(PATHS, key=lambda item: item["external_centerline_total_m"])
RAS_PATHS = []
for tank, centre in enumerate(SECONDARY_CENTRES, 1):
    series = (tank + 1) // 2
    target = A2O_CENTRES[series - 1]
    total = 36 + abs(centre - target) + 22
    RAS_PATHS.append({"secondary": tank, "series": series, "centerline_m": total})
WORST_RAS_PATH = max(RAS_PATHS, key=lambda item: item["centerline_m"])
WORST_AIR_PATH_M = 150 + 4


SPACING_CHECKS = [
    ("相邻平流初沉池占地包络", 37.0, "相邻中心距100−包络宽63", "通过；中间可布管和检修"),
    ("相邻A2/O系列占地包络", 25.0, "相邻中心距100−包络宽75", "通过；保持四系列独立检修面"),
    ("相邻二沉池暂定结构外缘", 6.2, "中心距44−暂定结构外径37.8", "通过；D42操作包络间另有2.0 m"),
    ("初沉池与A2/O占地包络", 28.0, "初沉南缘216−A2/O北缘188", "通过；含6 m道路和管线带"),
    ("A2/O与二沉池占地包络", 37.0, "A2/O南缘138−二沉北缘101", "通过；含配水井、风机房和6 m道路"),
    ("二沉池与南侧管理/消毒区", 19.0, "二沉南缘59−南区北缘40", "通过；含4 m次通道和绿化隔离"),
    ("二沉配水井与A2/O", 8.0, "A2/O南缘138−配水井北缘130", "通过；构造连接待详图"),
    ("鼓风机房与A2/O", 4.0, "A2/O南缘138−风机房北缘134", "课程总图通过；吊装和防火间距待专项确认"),
    ("主车道", 6.0, "课程教案采用值", "形成厂界环路和三条横向联系路"),
    ("次通道", 4.0, "课程教案采用值", "服务接触池、计量井和二沉池南侧"),
    ("管理区至最近二沉池包络", 19.0, "垂直净距；另有道路/绿化", "条件性通过；无风玫瑰，不作上风向结论"),
]


water_area = sum(u["width"] * u["height"] for u in UNITS if u["category"] == "water")
auxiliary_area = sum(u["width"] * u["height"] for u in UNITS if u["category"] in {"auxiliary", "management"})
future_area = sum(u["width"] * u["height"] for u in UNITS if u["category"] == "future")
road_area = rectangle_union_area(ROADS)
site_area = SITE_WIDTH * SITE_HEIGHT
unallocated = site_area - water_area - auxiliary_area - future_area - road_area
green_target = 36_000.0
other_available = unallocated - green_target
assert other_available > 0


SUMMARY = {
    "basis": {
        "input_git_commit": "02b4846",
        "site_m": [SITE_WIDTH, SITE_HEIGHT],
        "site_area_m2": site_area,
        "coordinate_system": "西南角(0,0)，x向东，y向北",
        "inlet_m": [360.0, 300.0],
        "outlet_boundary_m": [400.0, 29.0],
        "river_relation": "东厂界外接河道；厂外管线实测长度待定",
        "summer_prevailing_wind": "东南（任务书仅给主导方向，无风频风玫瑰）",
        "gates_m": {"south_main": [68.0, 0.0], "north_service": [200.0, 300.0]},
    },
    "counts": {
        "primary_clarifiers": 4,
        "a2o_series": 4,
        "secondary_distribution_wells": 2,
        "secondary_clarifiers": 8,
        "contact_tank_cells": 2,
    },
    "area_account_m2": {
        "water_envelopes": water_area,
        "auxiliary_and_management": auxiliary_area,
        "continuous_future": future_area,
        "road_union": road_area,
        "unallocated": unallocated,
        "provisional_green_target": green_target,
        "other_available": other_available,
        "total": site_area,
    },
    "control_paths": {
        "water": WORST_WATER_PATH,
        "all_water_paths": PATHS,
        "RAS": {"worst": WORST_RAS_PATH, "all": RAS_PATHS},
        "air_from_blower_to_farthest_series_m": WORST_AIR_PATH_M,
        "internal_recycle_each_series_plan_m": 80.0,
        "bypass_reserved_plan_m": length("EM"),
    },
    "engineering_route_length_by_system_m": {
        system: sum(r["length_m"] for r in ROUTES if r["system"] == system)
        for system in sorted({r["system"] for r in ROUTES})
    },
    "checks": [
        "all occupancy envelopes are inside the 400 m x 300 m boundary",
        "occupancy envelopes do not overlap each other or roads",
        "all route polylines are axis-aligned and inside the boundary",
        "two parallel treatment lines and eight secondary clarifiers are represented",
        "water, RAS, internal recycle, air, waste-sludge boundary and bypass interfaces are represented",
        "area account closes to 120000 m2",
    ],
}

assert math.isclose(sum(SUMMARY["area_account_m2"][key] for key in ("water_envelopes", "auxiliary_and_management", "continuous_future", "road_union", "unallocated")), site_area)
assert WORST_WATER_PATH["secondary"] == 1
assert math.isclose(WORST_WATER_PATH["external_centerline_total_m"], 826.0)
assert math.isclose(WORST_RAS_PATH["centerline_m"], 86.0)
assert len([u for u in UNITS if u["code"].startswith("T")]) == 8


def write_csvs() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "第07组_构筑物坐标.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["编号", "名称", "形状", "中心x_m", "中心y_m", "西边x_m", "南边y_m", "东西宽_m", "南北长_m", "工艺净尺寸", "暂定结构外缘", "功能区", "说明"])
        for u in UNITS:
            writer.writerow([u["code"], u["name"], u["shape"], u["cx"], u["cy"], u["x"], u["y"], u["width"], u["height"], u["net_size"], u["structural_size"], u["category"], u["note"]])

    with (OUT / "第07组_管线节点.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["管段编号", "管段名称", "节点序号", "节点编号", "x_m", "y_m", "节点类型", "系统"])
        for r in ROUTES:
            for index, (x, y) in enumerate(r["points"]):
                node_type = "起点" if index == 0 else "终点" if index == len(r["points"]) - 1 else "折点"
                writer.writerow([r["code"], r["name"], index + 1, f'{r["code"]}-N{index + 1:02d}', x, y, node_type, r["system"]])

    with (OUT / "第07组_管线中心线长度.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["管段编号", "管段名称", "系统", "规格", "设计流量", "折点坐标_m", "管道中心线长度_m", "转弯数", "说明"])
        for r in ROUTES:
            writer.writerow([r["code"], r["name"], r["system"], r["size"], r["design_flow"], json.dumps(r["points"], ensure_ascii=False), f'{r["length_m"]:.2f}', r["bends"], r["note"]])

    with (OUT / "第07组_控制路径汇总.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["控制路径", "水线", "A2O系列", "二沉池", "公共前处理_m", "前处理至初沉_m", "初沉至A2O_m", "A2O至二沉_m", "二沉至接触池_m", "接触池至东厂界_m", "外部中心线总长_m"])
        for p in PATHS:
            writer.writerow([p["path"], p["line"], p["series"], p["secondary"], p["common_m"], p["pretreatment_to_primary_m"], p["primary_to_a2o_m"], p["a2o_to_secondary_m"], p["secondary_to_contact_m"], p["contact_to_boundary_m"], p["external_centerline_total_m"]])

    with (OUT / "第07组_间距与道路校核.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["核对对象", "实际净距或宽度_m", "计算或依据", "结论"])
        writer.writerows(SPACING_CHECKS)

    (OUT / "第07组_面积与控制路径.json").write_text(json.dumps(SUMMARY, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def svg_rect(x: float, y: float, width: float, height: float, fill: str, stroke: str = "#46606a", dash: str = "") -> str:
    return f'<rect x="{25 + x}" y="{335 - y - height}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" stroke-width="0.45" stroke-dasharray="{dash}"/>'


def write_svg() -> None:
    colors = {
        "water": "#1976a3",
        "ras": "#8a4d28",
        "internal": "#7354a8",
        "air": "#00a6a6",
        "sludge": "#636363",
        "bypass": "#c43c35",
    }
    fills = {"water": "#d9edf7", "auxiliary": "#ffe9bd", "management": "#e8f3cf", "future": "#e5ddf4"}
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1500" viewBox="0 0 480 450">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/></marker></defs>',
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#20333c;font-size:3.3px}.small{font-size:2.8px}.legend{font-size:3px}</style>',
        '<rect width="480" height="450" fill="#fff"/>',
        '<text x="25" y="12" style="font-size:7px;font-weight:bold">第二次修改第07组：总平面与管线复核草案 · 400 m × 300 m</text>',
        '<text x="25" y="21">西南角(0,0)，x向东、y向北；北界进水(360,300)，东厂界出水(400,29)。尺寸单位：m。</text>',
        svg_rect(0, 0, SITE_WIDTH, SITE_HEIGHT, "#f6faef", "#173d35"),
    ]
    for road in ROADS:
        svg.append(svg_rect(road["x"], road["y"], road["width"], road["height"], "#d4d9dc", "#d4d9dc"))
    for u in UNITS:
        svg.append(svg_rect(u["x"], u["y"], u["width"], u["height"], fills[u["category"]], dash="2 1" if u["category"] in {"auxiliary", "management", "future"} else ""))
        if u["shape"] == "circle":
            svg.append(f'<circle cx="{25 + u["cx"]}" cy="{335 - u["cy"]}" r="18.9" fill="none" stroke="#507584" stroke-width="0.55"/>')
    for r in ROUTES:
        points = " ".join(f'{25 + x},{335 - y}' for x, y in r["points"])
        dash = ' stroke-dasharray="3 2"' if r["style"] == "dash" else ""
        marker = ' marker-end="url(#arrow)"' if r["system"] in {"water", "ras", "internal", "sludge", "bypass"} and r["points"][0] != r["points"][-1] else ""
        width = 0.75 if r["system"] == "water" else 0.5
        svg.append(f'<polyline points="{points}" fill="none" stroke="{colors[r["system"]]}" stroke-width="{width}"{dash}{marker} opacity="0.86"/>')
    for u in UNITS:
        label = u["code"] if u["width"] < 25 else f'{u["code"]} {u["name"]}'
        svg.append(f'<text x="{25 + u["cx"]}" y="{334 - u["cy"]}" text-anchor="middle">{escape(label)}</text>')
        if u["height"] >= 10:
            svg.append(f'<text class="small" x="{25 + u["cx"]}" y="{339 - u["cy"]}" text-anchor="middle">{u["width"]:g}×{u["height"]:g}</text>')
    svg.extend(
        [
            '<path d="M448 70 Q438 160 447 300" fill="none" stroke="#39aaca" stroke-width="2"/><text x="446" y="180">河道</text>',
            '<path d="M445 48 L445 28" stroke="#243e43" stroke-width="1" marker-end="url(#arrow)"/><text x="443" y="24">N</text>',
            '<path d="M462 108 L438 84" stroke="#b45f35" stroke-width="1" marker-end="url(#arrow)"/><text x="468" y="113" text-anchor="end">东南来风（无频率）</text>',
            '<path d="M85 335 v5 M97 335 v5" stroke="#355" stroke-width="1.2"/><text x="80" y="347">南侧主门(68,0)</text>',
            '<path d="M219 35 v-5 M231 35 v-5" stroke="#355" stroke-width="1.2"/><text x="205" y="27">北侧服务门(200,300)</text>',
            '<text x="25" y="347">图例：</text>',
            '<path d="M45 346 h18" stroke="#1976a3" stroke-width="1"/><text class="legend" x="65" y="347">主水线</text>',
            '<path d="M88 346 h18" stroke="#8a4d28"/><text class="legend" x="108" y="347">RAS</text>',
            '<path d="M130 346 h18" stroke="#7354a8" stroke-dasharray="3 2"/><text class="legend" x="150" y="347">内回流</text>',
            '<path d="M184 346 h18" stroke="#00a6a6"/><text class="legend" x="204" y="347">空气</text>',
            '<path d="M230 346 h18" stroke="#636363" stroke-dasharray="3 2"/><text class="legend" x="250" y="347">排泥边界</text>',
            '<path d="M294 346 h18" stroke="#c43c35" stroke-dasharray="3 2"/><text class="legend" x="314" y="347">事故超越预留</text>',
            '<rect x="370" y="342" width="12" height="7" fill="#d4d9dc"/><text class="legend" x="384" y="347">道路</text>',
            '<text x="25" y="360">蓝色方框为水处理单元；圆线为二沉池暂定结构外缘D37.8，D42方框为操作包络；黄色为辅助设施，绿色为管理区，紫色为发展用地。</text>',
            '<text x="25" y="370">主车道6 m形成厂界环路和三条横向联系路；南侧次通道4 m。道路宽度为课程采用值，消防转弯、净空和登高面需正式复核。</text>',
            '<text x="25" y="380">水线按两组并行：C1/C2—B1/B2—DWA—T1至T4；C3/C4—B3/B4—DWB—T5至T8。接触池后再计量并从东界出厂。</text>',
            '<text x="25" y="390">任务书给夏季主导风向东南但无风频风玫瑰；管理区按南门交通和功能分隔暂定，不声称已证实位于上风向。</text>',
            f'<text x="25" y="402">最不利外部主水线：{WORST_WATER_PATH["path"]}，中心线{WORST_WATER_PATH["external_centerline_total_m"]:.0f} m；最不利RAS平面86 m；空气最远154 m。</text>',
            f'<text x="25" y="412">占地：水线包络{water_area:.0f} + 辅助/管理{auxiliary_area:.0f} + 发展{future_area:.0f} + 道路{road_area:.0f} + 未分配{unallocated:.0f} = 120000 m²。</text>',
            '<text x="25" y="422">正式CAD/BIM须补埋深、交叉、阀门井、转弯半径、吊装、防火、除臭和厂外管；本图用于计算说明书复核及第08/09组接口。</text>',
            '<path d="M350 434 h50 M350 432 v4 M375 432 v4 M400 432 v4" stroke="#263c44" fill="none"/><text x="345" y="440">0</text><text x="372" y="440">25</text><text x="397" y="440">50 m</text>',
            '</svg>',
        ]
    )
    (OUT / "第07组_总平面草案.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the versioned CSV, JSON and SVG outputs")
    args = parser.parse_args()
    if args.write:
        write_csvs()
        write_svg()
        for path in sorted(OUT.glob("第07组_*")):
            print(path.relative_to(ROOT))
    else:
        print(json.dumps(SUMMARY, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
