"""Build the group-01 visible-comment register from the read-only snapshot."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = (
    ROOT / "第二次修改协作项目_2026-09-13" / "02_成果回收"
    / "第01组_基线与意见定位" / "第01组_源文件标色快照.json"
)
DEFAULT_OUTPUT = DEFAULT_SNAPSHOT.with_name("第01组_意见定位总表.csv")


EXCEL = {
    1: "10,A1", 2: "10,A1", 3: "1", 4: "B1", 5: "27", 6: "12", 7: "B1,40,C4",
    8: "2", 9: "11", 10: "13,A1", 11: "3,A4", 12: "4", 13: "5", 14: "14",
    15: "41,45,C4", 16: "15,37,41", 17: "16", 18: "16,17", 19: "42,45,C4",
    20: "18,42", 21: "19", 22: "6,A3", 23: "27", 24: "27", 25: "27", 26: "27",
    27: "27", 28: "27,C4", 29: "9,27", 30: "20,21", 31: "21", 32: "7,A2",
    33: "7,A2", 34: "34,B2", 35: "B2", 36: "8,C3", 37: "8", 38: "22",
    39: "44,45,C4", 40: "A4,44", 41: "23,24,A1", 42: "23,24,26", 43: "A1",
    44: "9", 45: "9", 46: "B2", 47: "B2", 48: "25,A3", 49: "25,A3", 50: "34,B2",
    51: "34,B2", 52: "B3", 53: "B2,B3", 54: "B2,B3", 55: "B2,B3", 56: "B2,B3",
    57: "B2,B3", 58: "B2,B3", 59: "B2,B3", 60: "B2,B3", 61: "B2,B3",
    62: "22", 63: "22", 64: "22", 65: "22", 66: "22,23",
}


def responsibility(index: int, text: str) -> str:
    if index in {1, 2, 10, 11, 12, 13, 43, 47}:
        return "02"
    if index in {5, 21, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 44, 45, 46, 48, 49}:
        return "03/04"
    if index in {14, 15, 16, 17, 18, 19, 20, 34, 35, 50, 51}:
        return "05"
    if index in {38, 41, 42, 62, 63, 64, 65, 66}:
        return "06"
    if index in set(range(36, 38)) | set(range(52, 62)):
        return "07"
    if index in {39, 40}:
        return "08"
    if index in {7, 15, 19, 28, 31, 39}:
        return "09"
    return "10"


def timestamp(index: int) -> str:
    if index in {1, 2, 10, 43}: return "00:21-00:55;03:37-04:11;11:48-12:18"
    if index in {5, 6, 9}: return "03:22-06:00"
    if index in {10, 11, 12, 13, 47}: return "08:23-12:18"
    if index in {14, 15, 16}: return "12:26-15:37"
    if index in {17, 18, 19, 20}: return "17:21-20:23"
    if index in {21}: return "20:23-21:34"
    if index in {22, 23, 24, 25, 26, 27, 29, 44, 45, 46, 48, 49}: return "22:57-28:46"
    if index in {30, 31, 32, 33}: return "28:53-30:30"
    if index in {34, 35, 50, 51}: return "31:27-33:33"
    if index in set(range(36, 38)) | set(range(52, 62)): return "34:31-35:11"
    if index in {38, 62, 63, 64, 65, 66}: return "37:30-40:13"
    if index in {39, 40}: return "40:19-41:37"
    if index in {41, 42}: return "33:52-34:17;41:31-46:05"
    return "见Excel事项与原稿标色"


def conclusion(index: int, colours: list[str]) -> str:
    if index in {1, 2, 10, 11, 20, 21, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 38, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66}:
        return "保留结构后改值/改正"
    if "红色高亮" in colours:
        return "删除或改正"
    return "改正"


def first_revision_status(index: int) -> str:
    if index in {2, 32, 40, 43, 48, 49}:
        return "仍有黄色标记，未完成"
    if index in {1, 41}:
        return "标记已清但3台工作泵文字仍残留，未完成"
    if index in {10, 20, 21, 23, 24, 25, 26, 27, 29, 30, 31, 33, 34, 35, 36, 38, 42, 44, 45, 46, 47, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66}:
        return "已改或已清标，但本轮仍需技术复核"
    return "已删除/已改/已清标"


def impact(index: int) -> str:
    group = responsibility(index, "")
    return {
        "02": "正文、公式、表格、设备、图3-1/图5-1",
        "03/04": "正文、公式、参数表、药剂/回流/曝气设备、图9-1",
        "05": "正文、尺寸表、高程接口、图6-1/图7-1/图11-1",
        "06": "配水表、接触池、流程图与终端图",
        "07": "管线表、坐标、管损与总平面",
        "08": "表14-1/14-2、水位与高程图",
        "09": "位图题注、尺寸和箭头",
        "10": "正文表述、目录、参考文献与终检",
    }[group]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    rows = []
    for index, context in enumerate(data["original_docx"]["contexts"], start=1):
        rows.append({
            "定位编号": f"W{index:02d}",
            "颜色": "+".join(context["colours"]),
            "原稿位置": context["location"],
            "原稿完整上下文": context["full_text"],
            "第一版现状": first_revision_status(index),
            "Excel编号": EXCEL[index],
            "老师意见时间码": timestamp(index),
            "责任组": responsibility(index, context["full_text"]),
            "处理结论": conclusion(index, context["colours"]),
            "影响范围": impact(index),
        })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    assert len(rows) == 66
    assert not any(not row["Excel编号"] for row in rows)
    print(f"wrote {len(rows)} visible contexts to {args.out}")


if __name__ == "__main__":
    main()
