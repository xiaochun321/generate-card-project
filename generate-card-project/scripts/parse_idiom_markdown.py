#!/usr/bin/env python3
"""Parse idiom-card Markdown source into JSON records."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SECTION_MAP = {
    "简单解释": "explanation",
    "故事讲述": "story",
    "家长提示": "tip",
}


def make_pinyin(text: str) -> str:
    try:
        from pypinyin import Style, pinyin
    except ImportError:
        return ""
    return " ".join(part[0] for part in pinyin(text, style=Style.TONE))


def parse_markdown(markdown: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    section_key: str | None = None
    buffer: list[str] = []

    def flush_section() -> None:
        nonlocal buffer
        if current is not None and section_key:
            current[section_key] = "\n".join(line.strip() for line in buffer).strip()
        buffer = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        m_title = re.match(r"^##\s+(.+?)\s*$", line)
        m_section = re.match(r"^###\s+(.+?)\s*$", line)

        if m_title:
            flush_section()
            if current:
                records.append(current)
            current = {"idiom": m_title.group(1).strip()}
            section_key = None
            continue

        if m_section:
            flush_section()
            section_key = SECTION_MAP.get(m_section.group(1).strip())
            continue

        if current is not None and section_key:
            buffer.append(raw_line)

    flush_section()
    if current:
        records.append(current)
    return records


def apply_series(records: list[dict[str, str]], prefix: str) -> None:
    width = max(2, len(str(len(records))))
    total = str(len(records)).zfill(width)
    for index, record in enumerate(records, start=1):
        record["series_number"] = f"{prefix}/{str(index).zfill(width)}" if prefix else f"{index}/{total}"
        record["pinyin"] = make_pinyin(record["idiom"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--series-prefix", default="")
    args = parser.parse_args()

    records = parse_markdown(args.source.read_text(encoding="utf-8"))
    apply_series(records, args.series_prefix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
