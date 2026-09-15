"""Correct September 15 vector figures and embed their rendered PNGs in Word.

Use bundled Python. Run ``校正图件.py`` after generating SVGs, render the PNGs,
then run ``校正图件.py --embed``. The Word update changes only image media bytes;
native OMML equations and all other DOCX package members are preserved.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile


HERE = Path(__file__).resolve().parent
FIGURES = HERE / "图件"
WORD = HERE / "某污水处理厂设计计算说明书_0915修改稿.docx"
FIGURE_KEYS = (
    "图3-1_", "图5-1_", "图6-1_", "图7-1_", "图8-1_", "图9-1_",
    "图10-1_", "图11-1_", "图12-1_", "图13-1_", "图14-1_", "图15-1_",
)


CORRECTIONS = {
    "图3-1_": (
        ('<rect x="720" y="595" width="235" height="90"',
         '<rect x="720" y="125" width="235" height="95"'),
        ('<text x="837.5" y="617"', '<text x="837.5" y="155"'),
        ('<text x="837.5" y="648"', '<text x="837.5" y="185"'),
        ('<text x="837.5" y="679"', '<text x="837.5" y="212"'),
        ('<line x1="840" y1="595" x2="883" y2="345" stroke="#000000" stroke-width="3" marker-end="url(#arr-orange)"/>',
         '<polyline points="883,220 883,286" fill="none" stroke="#000000" stroke-width="3" marker-end="url(#arr-orange)"/>'),
    ),
    "图9-1_": (
        ('5 mg/L名义剂量', '以有效氯计5 mg/L'),
    ),
    "图10-1_": (
        ('DN1200环状空气母管（常态最远154 m；单段隔离绕行826 m）',
         'DN1200环状空气母管（常态最远154 m；隔离绕行长度另行核定）'),
    ),
    "图11-1_": (
        ('<text x="470" y="370" text-anchor="middle" font-size="21" font-weight="700" fill="#000000">刮吸泥机旋转</text>',
         '<text x="500" y="365" text-anchor="middle" font-size="18" font-weight="700" fill="#000000">刮吸泥机旋转</text>'),
    ),
    "图13-1_": (
        ('>METER</text>', '>计</text>'),
        ('<text x="765" y="629.9" text-anchor="end" font-size="18" font-weight="700" fill="#000000">东界出水</text>',
         '<text x="790" y="629.9" text-anchor="end" font-size="16" font-weight="700" fill="#000000">东界出水</text>'),
        ('道路：6 m环路＋4 m次通道', '道路：6 m环路＋3条6 m横向路＋4 m次通道'),
        ('水线：2条并行</text>', '水线：2条并行；计=长喉计量渠</text>'),
    ),
    "图15-1_": (
        ('<polyline points="370,182 455,182 455,265" fill="none" stroke="#000000" stroke-width="4" marker-end="url(#arr-orange)"/>',
         '<polyline points="80,182 55,182 55,524.375" fill="none" stroke="#000000" stroke-width="4"/>\n'
         '<line x1="55" y1="304.375" x2="98" y2="304.375" stroke="#000000" stroke-width="4" marker-end="url(#arr-orange)"/>\n'
         '<line x1="55" y1="524.375" x2="98" y2="524.375" stroke="#000000" stroke-width="4" marker-end="url(#arr-orange)"/>'),
        ('平均不少于44.83 min', '平均工况46.08 min'),
        ('每格8.0 m为廊道净水宽，不包括隔墙；次氯酸钠商品液设计有效氯浓度100 g/L。',
         '每格净水宽8.0 m，不含隔墙；商品液有效氯100 g/L；峰时0.3375 m³/h；7 d库存37.80 m³，储罐2×20 m³工作容积。'),
    ),
}


def one_file(directory: Path, prefix: str, suffix: str) -> Path:
    found = sorted(directory.glob(prefix + "*" + suffix))
    if len(found) != 1:
        raise ValueError(f"Expected one {prefix}*{suffix} in {directory}, got {len(found)}")
    return found[0]


def correct_svg_dir(directory: Path = FIGURES) -> list[str]:
    """Apply only exact, idempotent edits to the six affected SVGs."""
    changed = []
    for prefix, substitutions in CORRECTIONS.items():
        figure = one_file(directory, prefix, ".svg")
        source = figure.read_text(encoding="utf-8")
        revised = source
        for old, new in substitutions:
            before = revised.count(old)
            if before == 1:
                revised = revised.replace(old, new, 1)
            elif before == 0 and revised.count(new) == 1:
                continue
            else:
                raise ValueError(f"Unexpected match count {before} for {figure.name}: {old}")
        if revised != source:
            figure.write_text(revised, encoding="utf-8")
            changed.append(figure.name)
    return changed


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def embed_pngs_into_word(directory: Path = FIGURES, word: Path = WORD) -> dict[str, str]:
    """Replace media by stable image1..image12 mapping, leaving XML byte-identical."""
    pngs = {i: one_file(directory, prefix, ".png") for i, prefix in enumerate(FIGURE_KEYS, 1)}
    replacements = {f"word/media/image{i}.png": png.read_bytes() for i, png in pngs.items()}
    with ZipFile(word) as src:
        members = src.namelist()
        media = [name for name in members if name.startswith("word/media/")]
        if set(media) != set(replacements):
            raise ValueError("Unexpected Word media mapping; refusing to alter native equations")
        changed = {name: sha256(src.read(name)) != sha256(data) for name, data in replacements.items()}
        if not any(changed.values()):
            return {name: "unchanged" for name in replacements}
        with NamedTemporaryFile(prefix="figure-sync-", suffix=".docx", dir=word.parent, delete=False) as tmp:
            temp_name = tmp.name
        try:
            with ZipFile(temp_name, "w") as dst:
                for item in src.infolist():
                    # zipfile mutates ZipInfo.header_offset on write, so a copy is
                    # required while the source archive remains open for checks.
                    dst.writestr(deepcopy(item), replacements.get(item.filename, src.read(item.filename)))
            with ZipFile(temp_name) as check:
                if check.testzip() is not None:
                    raise ValueError("DOCX ZIP integrity check failed")
                for name in members:
                    if name not in replacements and src.read(name) != check.read(name):
                        raise ValueError(f"Non-media DOCX member changed: {name}")
                for name, data in replacements.items():
                    if check.read(name) != data:
                        raise ValueError(f"Embedded PNG mismatch: {name}")
            os.replace(temp_name, word)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
    return {name: ("updated" if updated else "unchanged") for name, updated in changed.items()}


def verify(directory: Path = FIGURES, word: Path = WORD) -> None:
    from lxml import etree

    if len(list(directory.glob("*.svg"))) != 12 or len(list(directory.glob("*.png"))) != 12:
        raise ValueError("Expected 12 SVG and 12 PNG figures")
    for svg in directory.glob("*.svg"):
        etree.parse(str(svg))
    with ZipFile(word) as z:
        if z.testzip() is not None:
            raise ValueError("DOCX package integrity failed")
        for i, prefix in enumerate(FIGURE_KEYS, 1):
            png = one_file(directory, prefix, ".png")
            if z.read(f"word/media/image{i}.png") != png.read_bytes():
                raise ValueError(f"Word/PDF source image mismatch: {prefix}")
        xml = z.read("word/document.xml")
        root = etree.fromstring(xml)
        math = root.xpath("//*[local-name()='oMath']")
        if len(math) != 300:
            raise ValueError(f"Expected 300 native Word equations, found {len(math)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed", action="store_true", help="Embed rendered PNGs in the September 15 Word file")
    parser.add_argument("--check", action="store_true", help="Check 12 SVGs and Word media hashes")
    args = parser.parse_args()
    if args.check:
        verify()
        print("12幅图件、Word媒体及300个原生公式对象核验通过")
    elif args.embed:
        for name, state in embed_pngs_into_word().items():
            if state == "updated":
                print(f"{name}: {state}")
    else:
        print("已校正：" + "、".join(correct_svg_dir()))


if __name__ == "__main__":
    main()
