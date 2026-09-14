#!/usr/bin/env python3
"""Build the complete, editable figure set for second-revision batch 7.

The script treats the frozen group 02-08 JSON/CSV files as the only numeric
inputs.  It writes 1600 x 800 SVG sources, a machine-readable figure data
inventory, and (after PNG rendering) a Word working copy whose twelve existing
inline pictures are replaced in place.  The public Word source is never edited.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Iterable, Sequence
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "第二次修改协作项目_2026-09-13"
RECOVERY = PROJECT / "02_成果回收"
OUT = RECOVERY / "第09组_位图整图重绘"
SVG_DIR = OUT / "可编辑SVG"
PNG_DIR = OUT / "导出PNG"

INPUTS = {
    "g02": RECOVERY / "第02组_流量工艺顺序与提升系统" / "第02组_复算结果.json",
    "g03": RECOVERY / "第03组_脱氮除磷方法与参数" / "第03组_复算结果.json",
    "g04": RECOVERY / "第04组_A2O回流曝气与鼓风机" / "第04组_复算结果.json",
    "g05": RECOVERY / "第05组_沉砂初沉二沉结构" / "第05组_复算结果.json",
    "g06": RECOVERY / "第06组_二沉配水与消毒" / "第06组_复算结果.json",
    "g07_area": RECOVERY / "第07组_总平面坐标与管线" / "第07组_面积与控制路径.json",
    "g07_units": RECOVERY / "第07组_总平面坐标与管线" / "第07组_构筑物坐标.csv",
    "g07_routes": RECOVERY / "第07组_总平面坐标与管线" / "第07组_管线中心线长度.csv",
    "g08": RECOVERY / "第08组_全厂水力高程" / "第08组_复算结果.json",
}

PUBLIC_DOCX = PROJECT / "00_公共文件" / "某污水处理厂设计计算说明书_第一版修改稿.docx"
OUTPUT_DOCX = OUT / "某污水处理厂设计计算说明书_第二次修改_整图重绘工作稿.docx"

BLUE = "#1F4E79"
MID_BLUE = "#5B9BD5"
LIGHT_BLUE = "#DDEBF7"
PALE_BLUE = "#EEF5FA"
GREEN = "#548235"
LIGHT_GREEN = "#E2F0D9"
ORANGE = "#C55A11"
LIGHT_ORANGE = "#FCE4D6"
PURPLE = "#7030A0"
LIGHT_PURPLE = "#E4DFEC"
BROWN = "#843C0C"
GRAY = "#666666"
LIGHT_GRAY = "#E7E6E6"
DARK = "#20323F"
RED = "#C00000"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


@dataclass
class Svg:
    title: str
    subtitle: str

    def __post_init__(self) -> None:
        self.parts: list[str] = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="800" viewBox="0 0 1600 800">',
            """<defs>
              <marker id="arr-blue" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#1F4E79"/></marker>
              <marker id="arr-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#548235"/></marker>
              <marker id="arr-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#C55A11"/></marker>
              <marker id="arr-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#7030A0"/></marker>
              <marker id="arr-brown" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#843C0C"/></marker>
              <marker id="arr-dark" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#20323F"/></marker>
            </defs>""",
            """<style>
              text{font-family:"Songti SC","SimSun","Noto Sans CJK SC","Microsoft YaHei",sans-serif;fill:#20323F}
              .title{font-size:38px;font-weight:700}.subtitle{font-size:23px;fill:#49616F}
              .h{font-size:29px;font-weight:700}.body{font-size:24px}.small{font-size:20px}.tiny{font-size:17px}
            </style>""",
            '<rect width="1600" height="800" fill="#FFFFFF"/>',
        ]
        self.text(800, 43, self.title, 38, "middle", 700)
        self.text(800, 78, self.subtitle, 23, "middle", 400, "#49616F")
        self.line(55, 96, 1545, 96, "#B4C7D5", 2)

    def text(
        self,
        x: float,
        y: float,
        value: str,
        size: int = 24,
        anchor: str = "start",
        weight: int = 400,
        color: str = DARK,
        rotate: float | None = None,
    ) -> None:
        transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
        self.parts.append(
            f'<text x="{x:g}" y="{y:g}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" fill="{color}"{transform}>{escape(str(value))}</text>'
        )

    def multiline(
        self,
        x: float,
        y: float,
        lines: Sequence[str],
        size: int = 24,
        anchor: str = "middle",
        weight: int = 400,
        color: str = DARK,
        gap: float | None = None,
    ) -> None:
        gap = gap or size * 1.25
        for i, value in enumerate(lines):
            self.text(x, y + i * gap, value, size, anchor, weight, color)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "none",
        stroke: str = BLUE,
        sw: float = 3,
        rx: float = 0,
        dash: str | None = None,
        opacity: float | None = None,
    ) -> None:
        extras = ""
        if dash:
            extras += f' stroke-dasharray="{dash}"'
        if opacity is not None:
            extras += f' opacity="{opacity:g}"'
        self.parts.append(
            f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}"{extras}/>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: str = BLUE,
        sw: float = 3,
        arrow: bool = False,
        dash: str | None = None,
        opacity: float | None = None,
    ) -> None:
        marker = ""
        if arrow:
            key = {BLUE: "blue", GREEN: "green", ORANGE: "orange", PURPLE: "purple", BROWN: "brown"}.get(color, "dark")
            marker = f' marker-end="url(#arr-{key})"'
        extras = f' stroke-dasharray="{dash}"' if dash else ""
        if opacity is not None:
            extras += f' opacity="{opacity:g}"'
        self.parts.append(
            f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" stroke-width="{sw:g}"{marker}{extras}/>'
        )

    def polyline(
        self,
        points: Sequence[tuple[float, float]],
        color: str = BLUE,
        sw: float = 3,
        arrow: bool = False,
        dash: str | None = None,
        fill: str = "none",
        opacity: float | None = None,
    ) -> None:
        marker = ""
        if arrow:
            key = {BLUE: "blue", GREEN: "green", ORANGE: "orange", PURPLE: "purple", BROWN: "brown"}.get(color, "dark")
            marker = f' marker-end="url(#arr-{key})"'
        extras = f' stroke-dasharray="{dash}"' if dash else ""
        if opacity is not None:
            extras += f' opacity="{opacity:g}"'
        pts = " ".join(f"{x:g},{y:g}" for x, y in points)
        self.parts.append(
            f'<polyline points="{pts}" fill="{fill}" stroke="{color}" stroke-width="{sw:g}"{marker}{extras}/>'
        )

    def polygon(self, points: Sequence[tuple[float, float]], fill: str, stroke: str = BLUE, sw: float = 3) -> None:
        pts = " ".join(f"{x:g},{y:g}" for x, y in points)
        self.parts.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}"/>')

    def circle(self, cx: float, cy: float, r: float, fill: str = "white", stroke: str = BLUE, sw: float = 3) -> None:
        self.parts.append(f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}"/>')

    def box(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        lines: Sequence[str] = (),
        fill: str = LIGHT_BLUE,
        stroke: str = BLUE,
        title_size: int = 25,
        body_size: int = 20,
    ) -> None:
        self.rect(x, y, w, h, fill, stroke, 3, 10)
        all_lines = [title, *lines]
        gap = 31 if len(all_lines) <= 3 else 27
        y0 = y + h / 2 - gap * (len(all_lines) - 1) / 2 + 8
        for i, line in enumerate(all_lines):
            self.text(x + w / 2, y0 + i * gap, line, title_size if i == 0 else body_size, "middle", 700 if i == 0 else 400, stroke if i == 0 else DARK)

    def dim(self, x1: float, y1: float, x2: float, y2: float, label: str, offset: float = 20) -> None:
        self.line(x1, y1, x2, y2, GRAY, 1.5)
        if abs(y2 - y1) < abs(x2 - x1):
            self.line(x1, y1 - 8, x1, y1 + 8, GRAY, 1.5)
            self.line(x2, y2 - 8, x2, y2 + 8, GRAY, 1.5)
            self.text((x1 + x2) / 2, y1 + offset, label, 21, "middle", 400, GRAY)
        else:
            self.line(x1 - 8, y1, x1 + 8, y1, GRAY, 1.5)
            self.line(x2 - 8, y2, x2 + 8, y2, GRAY, 1.5)
            self.text(x1 + offset, (y1 + y2) / 2, label, 21, "middle", 400, GRAY, -90)

    def footer(self, value: str) -> None:
        self.line(55, 754, 1545, 754, "#D9E2E8", 2)
        self.text(60, 783, value, 19, "start", 400, "#526873")

    def write(self, path: Path) -> None:
        path.write_text("\n".join([*self.parts, "</svg>", ""]), encoding="utf-8")


FIGURES = [
    ("图3-1", "水线工艺流程及回流排泥接口", "图3-1_水线工艺流程及回流排泥接口"),
    ("图5-1", "两格进水井与六泵位计算图", "图5-1_两格进水井与六泵位计算图"),
    ("图6-1", "曝气沉砂池计算图", "图6-1_曝气沉砂池计算图"),
    ("图7-1", "平流式初次沉淀池平剖计算图", "图7-1_平流式初次沉淀池平剖计算图"),
    ("图8-1", "A²O单系列分区与回流泵接口图", "图8-1_A2O单系列分区与回流泵接口图"),
    ("图9-1", "投药与固体闭合边界图", "图9-1_投药与固体闭合边界图"),
    ("图10-1", "曝气与鼓风系统计算图", "图10-1_曝气与鼓风系统计算图"),
    ("图11-1", "二次沉淀池平剖计算图", "图11-1_二次沉淀池平剖计算图"),
    ("图12-1", "主要连接管渠与配水接口图", "图12-1_主要连接管渠与配水接口图"),
    ("图13-1", "厂区总平面与管线图", "图13-1_厂区总平面与管线图"),
    ("图14-1", "全厂水线高程控制图", "图14-1_全厂水线高程控制图"),
    ("图15-1", "接触消毒与计量终端图", "图15-1_接触消毒与计量终端图"),
]

CAPTION_REPLACEMENTS = {
    "图3-1 水线工艺流程及回流、排泥接口": "图3-1 水线工艺流程及回流、排泥接口",
    "图5-1 四格进水井与四泵位计算草图": "图5-1 两格进水井与六泵位计算图",
    "图6-1 曝气沉砂池计算草图": "图6-1 曝气沉砂池计算图",
    "图7-1 平流式初次沉淀池平剖计算草图": "图7-1 平流式初次沉淀池平剖计算图",
    "图8-1 A²/O单系列按比例分区草图": "图8-1 A²/O单系列分区与回流泵接口图",
    "图9-1 投药与固体闭合边界": "图9-1 投药与固体闭合边界图",
    "图10-1 曝气与鼓风系统计算草图": "图10-1 曝气与鼓风系统计算图",
    "图11-1 二次沉淀池平剖计算草图": "图11-1 二次沉淀池平剖计算图",
    "图12-1 主要连接管渠与配水接口": "图12-1 主要连接管渠与配水接口图",
    "图13-1 厂区总平面计算草图": "图13-1 厂区总平面与管线图",
    "图14-1 全厂水线高程控制草图": "图14-1 全厂水线高程控制图",
    "图15-1 接触消毒与计量终端计算草图": "图15-1 接触消毒与计量终端图",
}


def add_flow_arrow(svg: Svg, x1: float, x2: float, y: float, label: str = "") -> None:
    svg.line(x1, y, x2, y, BLUE, 4, True)
    if label:
        svg.text((x1 + x2) / 2, y - 13, label, 18, "middle", 400, GRAY)


def figure_03(data: dict) -> Svg:
    g02, g04, g06 = data["g02"], data["g04"], data["g06"]
    svg = Svg("图3-1  水线工艺流程及回流、排泥接口", f"Q平均=4500 m³/h；Kz=1.50；Q最高时={g02['flow']['peak_m3_h']:.0f} m³/h；全厂两条并行水线")
    names = [
        ("粗格栅", "2格"), ("进水井/提升", "2格·6泵4用2备"), ("细格栅", "2格"),
        ("曝气沉砂", "2座"), ("平流初沉", "4座"), ("A²/O", "4系列"),
        ("二沉配水", "2井×4支路"), ("辐流二沉", "8座D37"),
        ("接触消毒", "2格·NaOCl"), ("长喉计量", "2渠"), ("东厂界", "DN1500"),
    ]
    x0, y, w, gap = 65, 235, 118, 20
    centers = []
    for i, (name, sub) in enumerate(names):
        x = x0 + i * (w + gap)
        svg.box(x, y, w, 105, name, [sub], PALE_BLUE if i not in {5, 8} else LIGHT_GREEN, BLUE, 22, 17)
        centers.append((x + w / 2, y + 52.5))
        if i:
            add_flow_arrow(svg, x - gap + 2, x - 5, y + 52.5)
    svg.text(65, 195, "北界D1200进水", 22, "start", 700, BLUE)
    svg.line(45, y + 52.5, 60, y + 52.5, BLUE, 4, True)

    a2o_x = centers[5][0]
    secondary_x = centers[7][0]
    svg.polyline([(secondary_x, 350), (secondary_x, 520), (a2o_x, 520), (a2o_x, 345)], BROWN, 4, True)
    svg.text((secondary_x + a2o_x) / 2, 548, "回流污泥 RAS=0.75Q；6台4用2备；H=3.0 m", 22, "middle", 700, BROWN)
    svg.polyline([(a2o_x + 25, 345), (a2o_x + 25, 445), (a2o_x - 25, 445), (a2o_x - 25, 345)], PURPLE, 4, True)
    svg.text(a2o_x, 476, "混合液内回流 IR=2.50Q；6台4用2备；H=1.2 m", 21, "middle", 700, PURPLE)

    svg.box(450, 595, 225, 90, "80%甲醇", ["设备容量6.5 t/d", "投加至缺氧区"], LIGHT_ORANGE, ORANGE, 23, 18)
    svg.line(675, 640, a2o_x - 15, 345, ORANGE, 3, True)
    svg.box(720, 595, 235, 90, "40% FeCl₃", ["设备容量2.0 m³/d", "A²/O后、二沉前"], LIGHT_ORANGE, ORANGE, 23, 18)
    svg.line(840, 595, (centers[5][0] + centers[6][0]) / 2, 345, ORANGE, 3, True)
    svg.polyline([(centers[4][0], 345), (centers[4][0], 700), (1010, 700)], GRAY, 3, True, "9 6")
    svg.text(1018, 707, "初沉污泥与剩余污泥至排泥边界", 21, "start", 400, GRAY)
    svg.footer("流程顺序唯一化：粗格栅→提升→细格栅→沉砂→初沉→A²/O→二沉→接触消毒→计量→东厂界。")
    return svg


def figure_05(data: dict) -> Svg:
    pump = data["g08"]["pump"]
    svg = Svg("图5-1  两格进水井与六泵位计算图", f"每条水线2用1备；全厂6台4用2备；定速泵按台数与液位启停调节")
    for side, x in enumerate((100, 820), 1):
        svg.box(x, 150, 580, 430, f"第{side}格进水井 / 水线{'A' if side == 1 else 'B'}", ["净平面16 m×10 m；调节水深1.20 m", "有效调节容积192 m³"], "#F8FBFD", BLUE, 29, 22)
        svg.line(x + 35, 350, x + 545, 350, MID_BLUE, 4)
        svg.text(x + 50, 338, "最高运行水位 EL23.80 m", 20, "start", 400, MID_BLUE)
        svg.line(x + 35, 475, x + 545, 475, MID_BLUE, 3, False, "8 6")
        svg.text(x + 50, 465, "最低运行水位 EL22.60 m", 20, "start", 400, MID_BLUE)
        for j in range(3):
            cx = x + 155 + j * 135
            standby = j == 2
            svg.circle(cx, 410, 38, LIGHT_GRAY if standby else LIGHT_BLUE, GRAY if standby else BLUE, 3)
            svg.text(cx, 418, f"P{side}{j+1}", 22, "middle", 700, GRAY if standby else BLUE)
            svg.line(cx, 372, cx, 285, BLUE, 3)
            svg.line(cx, 285, x + 520, 285, BLUE, 3)
            svg.text(cx, 520, "备用" if standby else "工作", 19, "middle", 700, GRAY if standby else GREEN)
        svg.text(x + 290, 620, "单泵1687.5 m³/h；H=14 m；90 kW", 24, "middle", 700, DARK)
        svg.text(x + 290, 654, "单泵支管DN700；两泵汇合后每线DN1000", 21, "middle", 400, DARK)
        svg.line(x + 520, 285, x + 620, 285, BLUE, 4, True)
    svg.line(35, 365, 95, 365, BLUE, 4, True)
    svg.text(40, 340, "粗格栅来水", 20, "start", 400, BLUE)
    svg.text(800, 710, f"最不利所需扬程={pump['required_head_m']:.3f} m；采用{pump['selected_head_m']:.0f} m；细格栅前控制水位EL{pump['discharge_control_el_m']:.2f} m", 23, "middle", 700, RED)
    svg.footer("井内局部泵坑沿用EL19.80 m；采购阶段须复核泵曲线、NPSH、安装淹没深度和启停频率。")
    return svg


def figure_06(data: dict) -> Svg:
    grit = data["g05"]["grit"]
    geom = data["g08"]["geometry"]
    svg = Svg("图6-1  曝气沉砂池计算图", f"2座并联；单座净尺寸30.0 m×3.8 m×2.55 m；峰值单池流量0.9375 m³/s")
    svg.text(380, 135, "平面图", 28, "middle", 700, BLUE)
    svg.rect(80, 175, 600, 250, "#F8FBFD", BLUE, 4)
    svg.line(110, 300, 650, 300, BLUE, 5, True)
    svg.line(140, 225, 620, 225, ORANGE, 4, True)
    svg.line(620, 255, 140, 255, ORANGE, 4, True)
    svg.text(380, 210, "吸砂机沿池长往复运行", 22, "middle", 700, ORANGE)
    for i in range(13):
        svg.circle(120 + i * 42, 365, 5, MID_BLUE, MID_BLUE, 1)
    svg.text(380, 395, "单侧供气量6 L/(m·s)，池外设置砂水分离器", 21, "middle", 400, DARK)
    svg.dim(80, 465, 680, 465, "净长 L=30.0 m", 30)
    svg.dim(720, 175, 720, 425, "净宽 B=3.8 m", 30)

    svg.text(1160, 135, "横断面", 28, "middle", 700, BLUE)
    svg.rect(900, 175, 520, 380, "#F8FBFD", BLUE, 4)
    water_y, floor_y = 245, 505
    svg.rect(903, water_y, 514, floor_y - water_y, "#EAF5FB", "none", 0)
    svg.line(900, water_y, 1420, water_y, MID_BLUE, 5)
    svg.line(900, floor_y, 1420, floor_y, BLUE, 5)
    svg.text(920, water_y - 16, "主体水位 EL34.25 m", 22, "start", 700, MID_BLUE)
    svg.text(920, floor_y + 35, f"平底 EL{geom['grit_floor_m']:.2f} m；池内不设砂斗", 22, "start", 700, BLUE)
    svg.line(950, 335, 1370, 335, BLUE, 4, True)
    svg.text(1160, 320, f"v={grit['peak_velocity_m_s']:.4f} m/s", 22, "middle", 700, DARK)
    for i in range(11):
        svg.circle(960 + i * 39, 460, 5, MID_BLUE, MID_BLUE, 1)
    svg.dim(1460, water_y, 1460, floor_y, "有效水深2.55 m", 34)
    svg.text(1160, 610, f"峰时停留{grit['retention_peak_min']:.3f} min；平均停留{grit['retention_average_min']:.3f} min；入口控制水位EL34.55 m", 22, "middle", 400, DARK)
    svg.footer("结构口径：池底为平底，排砂至池外砂水分离器；池内不设局部砂斗。")
    return svg


def figure_07(data: dict) -> Svg:
    primary = data["g05"]["primary"]
    geom = data["g08"]["geometry"]
    svg = Svg("图7-1  平流式初次沉淀池平剖计算图", "4座并联；单池净尺寸58.0 m×14.5 m×3.5 m；桁车式刮泥机")
    svg.text(400, 135, "平面图", 28, "middle", 700, BLUE)
    svg.rect(70, 170, 690, 250, "#F8FBFD", BLUE, 4)
    svg.rect(90, 185, 42, 220, LIGHT_ORANGE, ORANGE, 3)
    svg.text(111, 302, "横向\n条形泥斗", 18, "middle", 700, ORANGE, -90)
    for i in range(12):
        x = 535 + i * 15
        svg.line(x, 210, x, 380, MID_BLUE, 2)
    svg.text(625, 400, "12条×14 m指形出水槽", 20, "middle", 400, MID_BLUE)
    svg.line(690, 290, 745, 290, BLUE, 4, True)
    svg.line(500, 245, 170, 245, BROWN, 4, True)
    svg.text(335, 225, "刮泥方向：坡向进水端泥斗", 21, "middle", 700, BROWN)
    svg.dim(70, 455, 760, 455, "净长 L=58.0 m", 30)
    svg.dim(795, 170, 795, 420, "净宽 B=14.5 m", 30)

    svg.text(1190, 135, "纵剖面", 28, "middle", 700, BLUE)
    svg.rect(865, 170, 650, 430, "#FFFFFF", BLUE, 3)
    svg.rect(868, 220, 644, 210, "#EAF5FB", "none", 0)
    svg.line(865, 220, 1515, 220, MID_BLUE, 5)
    svg.text(885, 205, "主体水位 EL33.05 m", 21, "start", 700, MID_BLUE)
    svg.line(1015, 425, 1485, 395, BROWN, 4)
    svg.polygon([(880, 425), (1015, 425), (980, 555), (920, 555)], LIGHT_ORANGE, ORANGE, 3)
    svg.line(1015, 425, 880, 425, BROWN, 4)
    svg.text(1240, 440, f"池底纵坡 i={primary['floor_slope']:.2f}，坡降0.58 m", 21, "middle", 700, BROWN)
    svg.text(1190, 385, "名义沉淀底 EL29.55 m", 21, "middle", 400, DARK)
    svg.text(935, 585, f"泥斗端坡底EL{geom['primary_slope_low_floor_m']:.2f} m；斗底EL{geom['primary_hopper_bottom_m']:.2f} m", 19, "start", 700, ORANGE)
    svg.text(1190, 645, f"横向贯通泥斗：上口14.5×3.0 m；下口14.5×0.8 m；深2.0 m；容积{primary['transverse_hopper']['volume_m3']:.2f} m³", 21, "middle", 400, DARK)
    svg.text(1190, 682, f"峰时表面负荷{primary['surface_load_peak_m3_m2_h']:.3f} m³/(m²·h)；停留{primary['retention_peak_h']:.3f} h；水平流速{primary['horizontal_velocity_peak_m_s']:.4f} m/s", 21, "middle", 400, DARK)
    svg.footer("条形泥斗沿14.5 m池宽贯通；下口不得再画成0.8 m×0.8 m方斗。图示尺寸为工艺净尺寸。")
    return svg


def figure_08(data: dict) -> Svg:
    a2o, ret = data["g04"]["a2o"], data["g04"]["return_flows"]
    svg = Svg("图8-1  A²/O单系列分区与回流泵接口图", "4个工艺系列；每系列70 m×45 m×5 m；两条水线成对设置共享备用接口")
    x0, y0, lane_w, lane_h = 70, 145, 910, 72
    zone_colors = [(0, 45, LIGHT_ORANGE, ORANGE, "厌氧"), (45, 189, LIGHT_GREEN, GREEN, "缺氧"), (189, 420, LIGHT_BLUE, BLUE, "好氧")]
    for lane in range(6):
        start, end = lane * 70, (lane + 1) * 70
        direction = 1 if lane % 2 == 0 else -1
        for z0, z1, fill, stroke, _ in zone_colors:
            lo, hi = max(start, z0), min(end, z1)
            if hi <= lo:
                continue
            local0, local1 = lo - start, hi - start
            if direction == 1:
                rx = x0 + lane_w * local0 / 70
            else:
                rx = x0 + lane_w * (1 - local1 / 70)
            rw = lane_w * (hi - lo) / 70
            svg.rect(rx, y0 + lane * lane_h, rw, lane_h, fill, stroke, 1)
        cy = y0 + lane * lane_h + lane_h / 2
        if direction == 1:
            svg.line(x0 + 35, cy, x0 + lane_w - 35, cy, BLUE, 3, True)
        else:
            svg.line(x0 + lane_w - 35, cy, x0 + 35, cy, BLUE, 3, True)
        if lane < 5:
            xturn = x0 + lane_w if direction == 1 else x0
            svg.line(xturn, cy, xturn, cy + lane_h, BLUE, 3)
    svg.rect(x0, y0, lane_w, lane_h * 6, "none", BLUE, 4)
    svg.text(525, 610, "单系列等效流长420 m：厌氧45 m（1.5 h）·缺氧144 m（4.8 h）·好氧231 m（7.7 h）", 22, "middle", 700, DARK)
    svg.text(525, 646, f"单系列有效容积{a2o['volume_each_m3']:.0f} m³；全厂{a2o['volume_total_m3']:.0f} m³；总HRT={a2o['hrt_average_h']:.2f} h；MLSS={a2o['MLSS_base_kg_m3']:.2f} kg/m³", 21, "middle", 400, DARK)

    svg.text(1260, 135, "每条水线共享备用切换示意", 27, "middle", 700, BLUE)
    for row, label in enumerate(("水线A：B1 / B2", "水线B：B3 / B4")):
        y = 175 + row * 245
        svg.rect(1040, y, 440, 205, "#F8FBFD", BLUE, 3, 10)
        svg.text(1260, y + 35, label, 24, "middle", 700, BLUE)
        svg.box(1070, y + 60, 120, 65, "系列1" if row == 0 else "系列3", [], LIGHT_BLUE, BLUE, 20, 17)
        svg.box(1330, y + 60, 120, 65, "系列2" if row == 0 else "系列4", [], LIGHT_BLUE, BLUE, 20, 17)
        for j, (cx, standby) in enumerate(((1130, False), (1390, False), (1260, True))):
            svg.circle(cx, y + 165, 27, LIGHT_GRAY if standby else LIGHT_GREEN, GRAY if standby else GREEN, 3)
            svg.text(cx, y + 172, "S" if standby else f"P{j+1}", 19, "middle", 700, GRAY if standby else GREEN)
        svg.line(1130, y + 138, 1130, y + 125, GREEN, 3, True)
        svg.line(1390, y + 138, 1390, y + 125, GREEN, 3, True)
        svg.polyline([(1260, y + 138), (1260, y + 130), (1190, y + 130)], GRAY, 2, True, "7 5")
        svg.polyline([(1260, y + 138), (1260, y + 130), (1330, y + 130)], GRAY, 2, True, "7 5")
    svg.text(1260, 680, f"RAS：{ret['RAS_pumps']['count']}台4用2备，1266 m³/h·台，H=3.0 m；IR：{ret['internal_recycle_pumps']['count']}台4用2备，4219 m³/h·台，H=1.2 m", 20, "middle", 700, DARK)
    svg.footer("每条水线的备用泵经共用取水廊道、隔离阀和止回设施择一接入两个系列；RAS和IR分别配置同类切换关系。")
    return svg


def figure_09(data: dict) -> Svg:
    g03, g04, g06 = data["g03"], data["g04"], data["g06"]
    solids = g04["solids_and_secondary_check"]
    svg = Svg("图9-1  投药与固体闭合边界图", "药剂按设备容量表达；生物固体库存、化学固体和排泥量采用第03/04组冻结口径")
    svg.box(90, 250, 230, 140, "80%甲醇", ["设备容量6.5 t/d", "投加点：缺氧区"], LIGHT_ORANGE, ORANGE, 28, 22)
    svg.box(430, 230, 260, 180, "A²/O 4系列", ["MLSS 3.50 kg/m³", "总有效容积63000 m³", "SRT 20 d"], LIGHT_BLUE, BLUE, 28, 21)
    svg.box(795, 250, 230, 140, "40% FeCl₃", ["设备容量2.0 m³/d", "A²/O后、二沉前"], LIGHT_ORANGE, ORANGE, 28, 22)
    svg.box(1135, 220, 350, 200, "二沉系统", ["8座D37", f"总MLSS {solids['total_MLSS_to_secondary_kg_m3']:.6f} kg/m³", f"峰值SLR {solids['SLR_peak_kg_m2_d']:.3f} kg/(m²·d)"], LIGHT_GREEN, GREEN, 28, 21)
    add_flow_arrow(svg, 320, 425, 320)
    add_flow_arrow(svg, 690, 790, 320)
    add_flow_arrow(svg, 1025, 1130, 320)
    svg.line(205, 390, 500, 460, ORANGE, 3, True)
    svg.text(230, 455, "外加COD容量单列", 20, "start", 400, ORANGE)
    svg.line(910, 390, 1185, 455, ORANGE, 3, True)
    svg.text(915, 450, f"化学干固体{solids['chemical_dry_solids_kg_d']:.3f} kg/d", 20, "start", 400, ORANGE)
    svg.box(480, 520, 290, 120, "固体库存", [f"基准220500 kg", f"化学库存{solids['chemical_inventory_kg_at_20d']:.3f} kg"], LIGHT_PURPLE, PURPLE, 26, 20)
    svg.box(1000, 520, 320, 120, "排泥边界", [f"总排固{solids['total_waste_solids_kg_d_at_20d']:.3f} kg/d", "VSS/ISS实测后再细分"], "#F2F2F2", GRAY, 26, 20)
    svg.line(560, 410, 615, 515, PURPLE, 3, True)
    svg.line(1310, 420, 1160, 515, GRAY, 3, True)
    svg.box(90, 540, 260, 100, "次氯酸钠", ["5 mg/L名义剂量", "15 mg/L设备容量→接触池"], LIGHT_ORANGE, ORANGE, 24, 19)
    svg.text(800, 700, f"FeCl₃化学固体使MLSS增加{solids['chemical_MLSS_increment_kg_m3']:.6f} kg/m³；平均/峰值SLR={solids['SLR_average_kg_m2_d']:.3f}/{solids['SLR_peak_kg_m2_d']:.3f} kg/(m²·d)", 21, "middle", 700, DARK)
    svg.footer("甲醇、FeCl₃和NaOCl均为缺测水质条件下的课程设备容量；最终运行剂量按在线监测、瓶试和消毒试验校准。")
    return svg


def figure_10(data: dict) -> Svg:
    aer = data["g04"]["aeration"]
    air08 = data["g08"]["air"]
    svg = Svg("图10-1  曝气与鼓风系统计算图", f"采用48000 Nm³/h（0℃、101325 Pa）；DN1200环状母管；4条DN700系列支管")
    svg.text(800, 135, "高速离心鼓风机 6台（4用2备）", 29, "middle", 700, BLUE)
    for i in range(6):
        cx = 385 + i * 165
        standby = i >= 4
        svg.circle(cx, 205, 48, LIGHT_GRAY if standby else LIGHT_BLUE, GRAY if standby else BLUE, 4)
        svg.text(cx, 198, f"B{i+1}", 23, "middle", 700, GRAY if standby else BLUE)
        svg.text(cx, 226, "备用" if standby else "工作", 18, "middle", 700, GRAY if standby else GREEN)
        svg.line(cx, 253, cx, 300, GRAY if standby else BLUE, 3, True, "8 5" if standby else None)
    svg.text(800, 282, "单台12000 Nm³/h；65 kPa(g)；参考AT 400-0.8 G5或等效", 22, "middle", 400, DARK)
    svg.rect(130, 315, 1340, 330, "none", BLUE, 5, 18)
    svg.text(800, 345, "DN1200环状空气母管（常态最远154 m；单段隔离绕行826 m）", 22, "middle", 700, BLUE)
    for i in range(4):
        x = 220 + i * 335
        svg.line(x + 120, 315, x + 120, 420, BLUE, 4, True)
        svg.box(x, 420, 240, 160, f"A²/O系列{i+1}", ["好氧区", "DN700支管", "2400盘×5 Nm³/h"], PALE_BLUE, BLUE, 25, 20)
        for r in range(3):
            for c in range(10):
                svg.circle(x + 25 + c * 21, 555 - r * 16, 3.5, MID_BLUE, MID_BLUE, 1)
    svg.text(800, 685, f"需气量{aer['air_required_Nm3_h_at_0C_101325Pa']:.0f} Nm³/h；采用48000；9600盘；供氧余量{aer['capacity_margin_fraction']*100:.2f}%", 22, "middle", 700, DARK)
    svg.text(800, 720, f"压力预算：静水46.60＋曝气器5＋管阀6＋余量3＝60.60 kPa；采用65 kPa；池内配气可用余量{air08['internal_distribution_budget_kPa']:.3f} kPa", 21, "middle", 400, DARK)
    svg.footer("标准风量基准必须随图标明；厂家按实际气压、湿度、入口温度、SOTE、喘振线和噪声重新确认工作点。")
    return svg


def figure_11(data: dict) -> Svg:
    sec = data["g05"]["secondary"]
    solids = data["g04"]["solids_and_secondary_check"]
    geom = data["g08"]["geometry"]
    svg = Svg("图11-1  二次沉淀池平剖计算图", "8座辐流式二沉池；净D37 m；中心井D6 m；周边传动刮吸泥机")
    svg.text(385, 140, "平面图", 28, "middle", 700, BLUE)
    svg.circle(385, 390, 225, "#F8FBFD", BLUE, 4)
    svg.circle(385, 390, 36, "white", BROWN, 3)
    svg.line(385, 390, 585, 390, BROWN, 4, True)
    svg.text(470, 370, "刮吸泥机旋转", 21, "middle", 700, BROWN)
    svg.dim(160, 655, 610, 655, "净径D=37 m", 32)
    svg.text(385, 700, f"净面积{sec['net_area_each_m2']:.2f} m²/座；中心井D6 m", 21, "middle", 400, DARK)

    svg.text(1160, 140, "径向剖面", 28, "middle", 700, BLUE)
    svg.rect(800, 175, 720, 425, "white", BLUE, 3)
    water_y = 235
    periph_floor_y = 470
    inner_floor_y = 555
    sump_bottom_y = 610
    svg.rect(803, water_y, 714, periph_floor_y - water_y, "#EAF5FB", "none", 0)
    svg.line(800, water_y, 1520, water_y, MID_BLUE, 5)
    svg.polygon([(800, periph_floor_y), (1025, periph_floor_y), (1105, inner_floor_y), (1415, inner_floor_y), (1495, periph_floor_y), (1520, periph_floor_y), (1520, 600), (800, 600)], "#F5E6D3", BROWN, 3)
    svg.polygon([(1105, inner_floor_y), (1200, inner_floor_y), (1220, sump_bottom_y), (1300, sump_bottom_y), (1320, inner_floor_y), (1415, inner_floor_y)], LIGHT_ORANGE, ORANGE, 3)
    svg.line(1260, 180, 1260, sump_bottom_y, BROWN, 4)
    svg.text(825, 220, "水位EL31.15 m", 21, "start", 700, MID_BLUE)
    svg.text(835, 462, "周边底EL27.15 m", 20, "start", 700, BROWN)
    svg.text(1080, 548, f"内缘底EL{geom['secondary_inner_floor_m']:.3f} m", 19, "start", 700, BROWN)
    svg.text(1225, 640, f"坑底EL{geom['secondary_sump_bottom_m']:.3f} m", 19, "start", 700, ORANGE)
    svg.text(1450, 285, "沉淀区3.10 m", 20, "end", 400, DARK)
    svg.text(1450, 355, "缓冲层0.50 m", 20, "end", 400, DARK)
    svg.text(1450, 420, "周边贮泥0.40 m", 20, "end", 400, DARK)
    svg.text(1060, 690, "周边总深4.00 m；坡降0.775 m；中心泥坑0.50 m；中心总深5.275 m", 21, "start", 700, DARK)
    svg.text(800, 725, f"峰时表面负荷{sec['surface_load_peak_m3_m2_h']:.3f} m³/(m²·h)；峰值SLR={solids['SLR_peak_kg_m2_d']:.3f} kg/(m²·d)", 21, "start", 400, DARK)
    svg.footer("净径D37与中心井D6均完整标注；水位与池底采用第08组最终高程。")
    return svg


def figure_12(data: dict) -> Svg:
    g06, g07 = data["g06"], data["g07_area"]
    svg = Svg("图12-1  主要连接管渠与配水接口图", "两条水线；2座二沉配水井×4条独立支管；清水汇合后DN1500至东厂界")
    top = [
        ("北界进水", "DN1200"), ("提升泵", "6台4用2备"), ("细格栅/沉砂", "2线"),
        ("初沉配水", "2井→4池"), ("A²/O", "4系列"), ("二沉配水", "2井×4支"),
        ("接触池", "2格"), ("长喉计量", "2渠"), ("东厂界", "DN1500"),
    ]
    x0, y, w, gap = 60, 145, 145, 27
    for i, (name, sub) in enumerate(top):
        x = x0 + i * (w + gap)
        svg.box(x, y, w, 90, name, [sub], PALE_BLUE, BLUE, 23, 18)
        if i:
            add_flow_arrow(svg, x - gap + 1, x - 5, y + 45)

    svg.text(
        800,
        274,
        "接口：进厂DN1200；单泵DN700、每线DN1000；初沉支管DN900；A²/O→配水井DN1200；入二沉DN900；出二沉DN700→DN1200；出厂DN1500",
        19,
        "middle",
        700,
        BLUE,
    )

    for group, gx in (("DWA", 110), ("DWB", 845)):
        svg.box(gx + 250, 330, 180, 95, group, ["接收2个A²/O系列", "4个1.20 m等高堰"], LIGHT_GREEN, GREEN, 25, 17)
        for j in range(4):
            cx = gx + j * 150
            svg.circle(cx + 60, 600, 48, "#F8FBFD", BLUE, 3)
            n = j + 1 + (0 if group == "DWA" else 4)
            svg.text(cx + 60, 608, f"T{n}", 22, "middle", 700, BLUE)
            start_x = gx + 280 + j * 35
            svg.polyline([(start_x, 425), (start_x, 500 + j * 8), (cx + 60, 500 + j * 8), (cx + 60, 548)], BLUE, 3, True)
            svg.text(cx + 60, 675, "DN900入池", 18, "middle", 400, BLUE)
        svg.text(gx + 285, 305, "2×DN1200来水", 20, "middle", 700, BLUE)
    svg.text(800, 720, f"每池峰值混合液{g06['distribution']['mixed_flow_peak_per_secondary_branch_m3_h']:.1f} m³/h；每池清水{g06['distribution']['external_flow_peak_per_secondary_outlet_m3_h']:.1f} m³/h；最不利外部水线{g07['control_paths']['water']['external_centerline_total_m']:.0f} m", 22, "middle", 700, DARK)
    svg.footer("图内DN为冻结课程内径；逐段长度、流量和转弯数以第07组CSV为准，埋管及竖向接口以第08组CSV为准。")
    return svg


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def figure_13(data: dict) -> Svg:
    units = read_csv(INPUTS["g07_units"])
    routes = read_csv(INPUTS["g07_routes"])
    g07 = data["g07_area"]
    svg = Svg("图13-1  厂区总平面与管线图", "厂界400 m×300 m（12 ha）；西南角为(0,0)，x向东、y向北")
    px, py, scale = 60, 125, 1.9
    pw, ph = 400 * scale, 300 * scale
    svg.rect(px, py, pw, ph, "#F6FAEF", "#173D35", 4)
    roads = [(6, 6, 388, 6), (6, 288, 388, 6), (6, 6, 6, 288), (388, 6, 6, 288), (6, 108, 388, 6), (6, 204, 388, 6), (6, 242, 388, 6), (6, 48, 388, 4)]
    for x, y, w, h in roads:
        svg.rect(px + x * scale, py + (300 - y - h) * scale, w * scale, h * scale, "#D4D9DC", "#D4D9DC", 1)
    colors = {"water": LIGHT_BLUE, "auxiliary": "#FFE9BD", "management": LIGHT_GREEN, "future": LIGHT_PURPLE}
    for u in units:
        x, y, w, h = map(float, (u["西边x_m"], u["南边y_m"], u["东西宽_m"], u["南北长_m"]))
        sx, sy = px + x * scale, py + (300 - y - h) * scale
        cat = u["功能区"]
        svg.rect(sx, sy, w * scale, h * scale, colors.get(cat, "white"), BLUE if cat == "water" else GRAY, 1.8, 0, "7 5" if cat != "water" else None)
        if u["形状"] == "circle":
            svg.circle(px + float(u["中心x_m"]) * scale, py + (300 - float(u["中心y_m"])) * scale, 18.9 * scale, "none", "#507584", 1.5)
    route_colors = {"water": "#1976A3", "ras": BROWN, "internal": PURPLE, "air": "#00A6A6", "sludge": GRAY, "bypass": RED}
    for r in routes:
        system = r["系统"]
        if system not in route_colors:
            continue
        points = json.loads(r["折点坐标_m"])
        pts = [(px + float(x) * scale, py + (300 - float(y)) * scale) for x, y in points]
        svg.polyline(pts, route_colors[system], 2.3 if system == "water" else 1.5, False, "7 5" if system in {"internal", "sludge", "bypass"} else None, opacity=0.82)
    for u in units:
        if u["编号"] in {"FUT", "AIR", "CHEM", "ADMIN", "MAINT", "NAOCL", "CT", "METER", "G1", "P", "G2", "PDA", "PDB", "DWA", "DWB"} or u["编号"].startswith(("C", "B", "T")):
            svg.text(px + float(u["中心x_m"]) * scale, py + (300 - float(u["中心y_m"])) * scale + 7, u["编号"], 14 if u["编号"].startswith("T") else 16, "middle", 700, DARK)
    svg.line(px + 360 * scale, py - 20, px + 360 * scale, py + 5, BLUE, 3, True)
    svg.text(px + 360 * scale, py - 28, "北界进水(360,300)", 18, "middle", 700, BLUE)
    svg.line(px + pw - 45, py + (300 - 29) * scale, px + pw - 4, py + (300 - 29) * scale, BLUE, 3, True)
    svg.text(px + pw - 55, py + (300 - 29) * scale - 10, "东界出水", 18, "end", 700, BLUE)
    svg.text(px + 25, py + 30, "连续发展用地", 16, "start", 700, PURPLE)
    svg.text(px + pw + 30, py + 60, "N", 22, "middle", 700, DARK)
    svg.line(px + pw + 30, py + 100, px + pw + 30, py + 68, DARK, 3, True)

    rx = 890
    svg.text(rx, 145, "图例与控制数据", 29, "start", 700, BLUE)
    legends = [("主水线", "#1976A3", None), ("RAS", BROWN, None), ("内回流", PURPLE, "7 5"), ("空气", "#00A6A6", None), ("排泥边界", GRAY, "7 5"), ("事故超越", RED, "7 5")]
    for i, (label, color, dash) in enumerate(legends):
        yy = 190 + i * 42
        svg.line(rx, yy, rx + 75, yy, color, 4, False, dash)
        svg.text(rx + 95, yy + 8, label, 22, "start", 400, DARK)
    notes = [
        "水线：2条并行", "平流初沉池：4座58×14.5 m", "A²/O：4系列70×45×5 m",
        "二沉：2配水井×4池；8座D37", "接触池：2格45×8×4.8 m", "道路：6 m环路＋4 m次通道",
        f"最不利主水线：{g07['control_paths']['water']['external_centerline_total_m']:.0f} m", "最不利RAS：86 m；空气常态最远154 m",
        "夏季东南来风，无风频风玫瑰", "厂外至河道长度待实测",
    ]
    svg.multiline(rx, 470, notes, 22, "start", 400, DARK, 30)
    svg.footer("构筑物包络、节点和折点可由第07组CSV复建；本图为课程说明书总图，正式CAD/BIM仍须完成地下管线综合与专项审查。")
    return svg


def figure_14(data: dict) -> Svg:
    g08 = data["g08"]
    stages = g08["stages"]
    names = [stages[0]["start"], *[s["end"] for s in stages]]
    levels = [stages[0]["upstream_el_m"], *[s["downstream_el_m"] for s in stages]]
    svg = Svg("图14-1  全厂水线高程控制图", "最不利重力路径T1；细格栅前至计量后落差5.50 m；延伸东厂界后总落差6.05 m")
    x0, x1, y0, y1 = 90, 1510, 135, 410
    el_min, el_max = 28.5, 35.0
    def yy(el: float) -> float:
        return y0 + (el_max - el) / (el_max - el_min) * (y1 - y0)
    for el in (35, 34, 33, 32, 31, 30, 29):
        y = yy(el)
        svg.line(x0, y, x1, y, "#D9E2E8", 1.2, False, "5 5")
        svg.text(x0 - 12, y + 7, f"EL{el:.0f}", 17, "end", 400, GRAY)
    xs = [x0 + i * (x1 - x0) / (len(levels) - 1) for i in range(len(levels))]
    pts: list[tuple[float, float]] = [(xs[0], yy(levels[0]))]
    for i in range(1, len(levels)):
        pts.extend([(xs[i], yy(levels[i - 1])), (xs[i], yy(levels[i]))])
    svg.polyline(pts, BLUE, 5)
    for i, (x, el) in enumerate(zip(xs, levels)):
        svg.circle(x, yy(el), 8, "white", BLUE, 3)
        svg.text(x, yy(el) - 14, str(i), 16, "middle", 700, BLUE)
    svg.text(120, 455, f"提升泵：进水井最低EL{g08['pump']['suction_min_el_m']:.2f} → 细栅前EL{g08['pump']['discharge_control_el_m']:.2f}；H需={g08['pump']['required_head_m']:.3f} m，采用14 m", 22, "start", 700, RED)
    svg.text(1480, 455, f"闭合误差={g08['closure_error_m']:.2e} m", 20, "end", 400, GRAY)
    labels = [(i, names[i].replace("A2O", "A²/O"), levels[i]) for i in range(len(names))]
    for row in range(2):
        start = row * 10
        for col in range(10):
            idx = start + col
            if idx >= len(labels):
                continue
            x, y, w, h = 70 + col * 148, 490 + row * 112, 142, 96
            fill = PALE_BLUE if idx % 2 == 0 else "#F8FBFD"
            svg.rect(x, y, w, h, fill, "#A6B9C7", 1.5, 5)
            i, name, el = labels[idx]
            svg.text(x + 8, y + 24, f"{i}", 17, "start", 700, BLUE)
            shown = name if len(name) <= 7 else name[:7]
            svg.text(x + w / 2, y + 53, shown, 17, "middle", 400, DARK)
            svg.text(x + w / 2, y + 80, f"EL{el:.2f}", 19, "middle", 700, BLUE)
    svg.footer("图中落差含构筑物预算、连接损失、调节及余量；6.05 m不得解释为纯摩擦损失或未经调节的自然水面。")
    return svg


def draw_serpentine(svg: Svg, x: float, y: float, w: float, h: float, label: str) -> None:
    svg.rect(x, y, w, h, "#F8FBFD", BLUE, 3)
    lane = h / 4
    for i in range(1, 4):
        if i % 2:
            svg.line(x + w * 0.78, y + (i - 1) * lane, x + w * 0.78, y + i * lane, GRAY, 3)
        else:
            svg.line(x + w * 0.22, y + (i - 1) * lane, x + w * 0.22, y + i * lane, GRAY, 3)
    for i in range(4):
        cy = y + (i + 0.5) * lane
        if i % 2 == 0:
            svg.line(x + 25, cy, x + w - 25, cy, BLUE, 3, True)
        else:
            svg.line(x + w - 25, cy, x + 25, cy, BLUE, 3, True)
    svg.text(x + w / 2, y - 14, label, 22, "middle", 700, BLUE)


def figure_15(data: dict) -> Svg:
    contact, dis, meter = data["g06"]["contact_tank"], data["g06"]["disinfection"], data["g08"]["meter"]
    svg = Svg("图15-1  接触消毒与计量终端图", "流程：二沉出水→NaOCl投加→2格接触池→2条长喉量水渠→汇合井→东厂界")
    svg.box(80, 130, 290, 105, "次氯酸钠投加", ["名义5 mg/L；设备15 mg/L", "计量泵2台（1用1备）×1.0 m³/h"], LIGHT_ORANGE, ORANGE, 25, 18)
    svg.polyline([(370, 182), (455, 182), (455, 265)], ORANGE, 4, True)
    draw_serpentine(svg, 80, 285, 720, 155, "接触池第1格：45 m×8 m净水宽×4.8 m")
    draw_serpentine(svg, 80, 505, 720, 155, "接触池第2格：45 m×8 m净水宽×4.8 m")
    svg.text(440, 700, f"每格4廊道×2.0 m；总净容积{contact['net_volume_total_m3']:.0f} m³；峰时接触{contact['contact_time_peak_min']:.2f} min；平均不少于{data['g08']['contact']['average_minimum_contact_min']:.2f} min", 21, "middle", 700, DARK)
    for row, y in enumerate((300, 520), 1):
        svg.line(800, y + 62, 915, y + 62, BLUE, 4, True)
        svg.polygon([(915, y + 25), (1040, y + 25), (1100, y + 43), (1100, y + 81), (1040, y + 99), (915, y + 99)], PALE_BLUE, BLUE, 3)
        svg.rect(1100, y + 43, 155, 38, LIGHT_GREEN, GREEN, 3)
        svg.polygon([(1255, y + 43), (1370, y + 25), (1470, y + 25), (1470, y + 99), (1370, y + 99), (1255, y + 81)], PALE_BLUE, BLUE, 3)
        svg.text(1190, y + 15, f"第{row}条长喉量水渠", 21, "middle", 700, BLUE)
        svg.text(1178, y + 70, "b=1.5 m；L=2.5 m", 18, "middle", 700, GREEN)
    svg.text(1195, 135, "峰时单渠Q=0.9375 m³/s", 24, "middle", 700, BLUE)
    svg.multiline(940, 175, [
        f"接触池入口/出口：EL30.25 / {data['g08']['contact']['peak_outlet_depth_m']+25.3:.2f}",
        f"计量上游/下游：EL{meter['approach_peak_el_m']:.2f} / {meter['downstream_peak_el_m']:.2f}",
        f"临界水深yc={meter['critical_depth_peak_m']:.3f} m",
        f"喉底EL{meter['throat_floor_el_m']:.3f}；临界水面EL{meter['throat_peak_water_el_m']:.3f}",
    ], 20, "start", 400, DARK, 28)
    svg.footer("8.0 m为每格净水宽；含3道0.20 m隔墙时结构池内总宽至少8.60 m。量水槽标定及余氯控制由厂家和试验复核。")
    return svg


def build_all() -> tuple[dict, list[dict]]:
    data = {key: read_json(path) for key, path in INPUTS.items() if path.suffix == ".json"}
    # Upstream cross-checks that prevent old values from silently reappearing.
    assert data["g02"]["flow"]["peak_m3_h"] == 6750.0
    assert data["g02"]["pump_scheme"]["count"] == 6
    assert data["g04"]["basis"]["series"] == 4
    assert data["g04"]["aeration"]["diffuser"]["count"] == 9600
    assert data["g04"]["aeration"]["blower"]["count"] == 6
    assert data["g05"]["primary"]["type"] == "平流式"
    assert data["g05"]["secondary"]["count"] == 8
    assert data["g06"]["distribution"]["well_count"] == 2
    assert data["g06"]["distribution"]["secondary_pools_per_well"] == 4
    assert math.isclose(data["g08"]["total_drop_to_boundary_m"], 6.05)
    builders = [figure_03, figure_05, figure_06, figure_07, figure_08, figure_09, figure_10, figure_11, figure_12, figure_13, figure_14, figure_15]
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    inventory: list[dict] = []
    data_lines = {
        "图3-1": ["Qavg=4500 m3/h", "Kz=1.50", "Qmax=6750 m3/h", "两条水线", "RAS=0.75Q", "IR=2.50Q"],
        "图5-1": ["两格进水井", "每格16x10x1.2 m", "192 m3/格", "6台4用2备", "1687.5 m3/h·台", "H=14 m", "90 kW"],
        "图6-1": ["2座", "30x3.8x2.55 m", "主体水位EL34.25", "平底EL31.70", "无池内砂斗"],
        "图7-1": ["4座平流式", "58x14.5x3.5 m", "水位EL33.05", "坡底EL28.97", "斗底EL26.97", "贯通条形斗55.10 m3"],
        "图8-1": ["4系列", "70x45x5 m", "63000 m3", "等效流长45/144/231 m", "RAS/IR各6台4用2备"],
        "图9-1": ["甲醇6.5 t/d", "40% FeCl3 2.0 m3/d", "化学干固体751.747 kg/d", "总MLSS3.738650 kg/m3", "总排固11776.747 kg/d"],
        "图10-1": ["48000 Nm3/h", "9600盘", "6台4用2备", "12000 Nm3/h·台", "65 kPa(g)", "DN1200/DN700"],
        "图11-1": ["8座D37", "中心井D6", "水位EL31.15", "周边底EL27.15", "内缘EL26.375", "坑底EL25.875", "SLRmax126.683"],
        "图12-1": ["2井x4池", "8条独立DN900", "8xDN700出水", "2xDN1200汇流", "DN1500出厂", "最不利水线826 m"],
        "图13-1": ["400x300 m", "33个包络", "75条管线折线", "6 m环路", "4 m次通道", "东南来风无频率"],
        "图14-1": ["细栅前EL34.80", "计量后EL29.30", "东界EL28.75", "总落差6.05 m", "Hrequired13.678 m", "Hselected14 m"],
        "图15-1": ["2格45x8x4.8 m", "4廊道/格", "峰时30.72 min", "2条b1.5xL2.5 m长喉渠", "yc0.341 m", "接触后计量"],
    }
    for index, ((number, caption, stem), builder) in enumerate(zip(FIGURES, builders), 1):
        svg_path = SVG_DIR / f"{stem}.svg"
        builder(data).write(svg_path)
        inventory.append({
            "figure": number,
            "caption": caption,
            "word_media": f"word/media/image{index}.png",
            "svg": str(svg_path.relative_to(ROOT)),
            "png": str((PNG_DIR / f"{stem}.png").relative_to(ROOT)),
            "data": data_lines[number],
        })
    inventory_doc = {
        "input_git_commit": "16e68a8",
        "canvas_px": [1600, 800],
        "input_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in INPUTS.values()},
        "figures": inventory,
    }
    (OUT / "第09组_图内数据清单.json").write_text(json.dumps(inventory_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data, inventory


def package_word(inventory: list[dict]) -> None:
    missing = [item["png"] for item in inventory if not (ROOT / item["png"]).is_file()]
    if missing:
        raise SystemExit(f"PNG files are missing; render SVG first: {missing}")
    replacements = {item["word_media"]: (ROOT / item["png"]).read_bytes() for item in inventory}
    OUT.mkdir(parents=True, exist_ok=True)
    with ZipFile(PUBLIC_DOCX, "r") as source, ZipFile(OUTPUT_DOCX, "w") as target:
        names = set(source.namelist())
        if not set(replacements).issubset(names):
            raise ValueError("Word source does not contain the expected twelve media targets")
        document = etree.fromstring(source.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        captions_changed = 0
        for paragraph in document.xpath(".//w:p", namespaces=ns):
            text_nodes = paragraph.xpath(".//w:t", namespaces=ns)
            paragraph_text = "".join(node.text or "" for node in text_nodes)
            replacement = CAPTION_REPLACEMENTS.get(paragraph_text)
            if replacement is None or not text_nodes:
                continue
            text_nodes[0].text = replacement
            for node in text_nodes[1:]:
                node.text = ""
            captions_changed += 1
        if captions_changed != len(CAPTION_REPLACEMENTS):
            raise ValueError(f"Expected {len(CAPTION_REPLACEMENTS)} captions, changed {captions_changed}")
        document_xml = etree.tostring(
            document,
            encoding="UTF-8",
            xml_declaration=True,
            standalone=True,
        )
        for info in source.infolist():
            payload = replacements.get(info.filename)
            if payload is None:
                payload = document_xml if info.filename == "word/document.xml" else source.read(info.filename)
            target.writestr(info, payload, compress_type=ZIP_DEFLATED)
    rows = []
    with ZipFile(PUBLIC_DOCX, "r") as old, ZipFile(OUTPUT_DOCX, "r") as new:
        for index, item in enumerate(inventory, 1):
            media = item["word_media"]
            old_hash = hashlib.sha256(old.read(media)).hexdigest()
            new_hash = hashlib.sha256(new.read(media)).hexdigest()
            if old_hash == new_hash:
                raise ValueError(f"Replacement did not change {media}")
            rows.append({
                "图号": item["figure"], "章节图题": item["caption"], "Word媒体位": media,
                "原图SHA256": old_hash, "新图SHA256": new_hash,
                "可编辑源": item["svg"], "导出PNG": item["png"], "像素": "1600×800",
            })
    with (OUT / "第09组_图片替换清单.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write SVG sources and data inventory")
    parser.add_argument("--package-word", action="store_true", help="replace the twelve Word media parts after PNG rendering")
    args = parser.parse_args()
    _, inventory = build_all()
    if args.package_word:
        package_word(inventory)
    if not args.write and not args.package_word:
        print(json.dumps({"figures": len(inventory), "canvas_px": [1600, 800], "output": str(OUT.relative_to(ROOT))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
