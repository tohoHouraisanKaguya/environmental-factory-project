#!/usr/bin/env python3
"""Ensure Word updates fields when opening a DOCX without changing body content."""

from __future__ import annotations

import argparse
import os
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W_NS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    args = parser.parse_args()
    docx = args.docx.resolve()

    with zipfile.ZipFile(docx, "r") as source:
        settings = ET.fromstring(source.read("word/settings.xml"))
        update = settings.find(f"{{{W_NS}}}updateFields")
        if update is None:
            update = ET.SubElement(settings, f"{{{W_NS}}}updateFields")
        update.set(f"{{{W_NS}}}val", "true")
        settings_xml = ET.tostring(settings, encoding="utf-8", xml_declaration=True)

        fd, temp_name = tempfile.mkstemp(suffix=".docx", dir=docx.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            with zipfile.ZipFile(temp, "w") as target:
                for item in source.infolist():
                    payload = settings_xml if item.filename == "word/settings.xml" else source.read(item.filename)
                    target.writestr(item, payload)
            temp.replace(docx)
        finally:
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
