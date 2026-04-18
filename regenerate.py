#!/usr/bin/env python3
"""
regenerate.py — Scan this folder for HTML pieces and rebuild the sidebar in index.html.

Usage:
    python3 regenerate.py

How it finds content:
    For every .html file in this folder (except index.html), the script reads
    these optional <meta> tags from its <head>:

        <meta name="category"       content="War">
        <meta name="subcategory"    content="WWII">
        <meta name="nav-title"      content="The Second World War">
        <meta name="nav-description" content="A short overview.">
        <meta name="nav-added"      content="2026-04-18">

    If a file has no meta tags, it falls back to:
      - _overrides.json (if present, keyed by filename) — hand-curated overrides
      - the file's <title>, then "Uncategorized"

    Files listed in _overrides.json with explicit title / category / subcategory
    always win, even over the file's own meta tags.

The script rewrites the block between the two marker lines inside index.html:
    // MANIFEST_START    ...    // MANIFEST_END
Everything outside the markers is preserved byte-for-byte.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
OVERRIDES = ROOT / "_overrides.json"

# Match <meta name="..." content="..."> where name's quote type must match
# its closer, and content can contain the *other* quote type (e.g. an
# apostrophe inside a double-quoted content value).
META_RE = re.compile(
    r'''<meta\s+name=(?P<nq>["\'])(?P<name>[^"\']+)(?P=nq)'''
    r'''\s+content=(?P<cq>["\'])(?P<content>.*?)(?P=cq)\s*/?\s*>''',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(r"<title>([^<]*)</title>", re.IGNORECASE)

MARK_START = "// MANIFEST_START"
MARK_END = "// MANIFEST_END"


def parse_html(path: Path) -> dict:
    """Pull meta tags and <title> out of an HTML file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  ! could not read {path.name}: {e}", file=sys.stderr)
        return {}
    metas = {m.group("name").lower(): m.group("content") for m in META_RE.finditer(text)}
    title_m = TITLE_RE.search(text)
    if title_m:
        metas["_title"] = title_m.group(1).strip()
    return metas


def load_overrides() -> dict:
    if not OVERRIDES.exists():
        return {}
    try:
        return json.loads(OVERRIDES.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ! _overrides.json is not valid JSON: {e}", file=sys.stderr)
        return {}


def build_entry(path: Path, overrides: dict) -> dict:
    meta = parse_html(path)
    override = overrides.get(path.name, {}) or {}

    def pick(*keys, default=""):
        for k in keys:
            if k in override and override[k]:
                return override[k]
        for k in keys:
            if k in meta and meta[k]:
                return meta[k]
        return default

    title = (
        override.get("title")
        or meta.get("nav-title")
        or meta.get("_title")
        or path.stem.replace("_", " ")
    )
    description = (
        override.get("description")
        or meta.get("nav-description")
        or meta.get("description")
        or ""
    )
    category = override.get("category") or meta.get("category") or "Uncategorized"
    subcategory = override.get("subcategory") or meta.get("subcategory") or "_default"
    added = (
        override.get("added")
        or meta.get("nav-added")
        or _dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    )
    return {
        "title": title.strip(),
        "file": path.name,
        "description": description.strip(),
        "added": added,
        "_category": category.strip(),
        "_subcategory": subcategory.strip(),
    }


def group(entries: list[dict]) -> list[dict]:
    """Fold flat entries into category/subcategory structure, preserving insertion order."""
    cats: dict[str, dict[str, list[dict]]] = {}
    cat_order: list[str] = []
    sub_order: dict[str, list[str]] = {}

    for e in entries:
        c = e["_category"]
        s = e["_subcategory"]
        if c not in cats:
            cats[c] = {}
            cat_order.append(c)
            sub_order[c] = []
        if s not in cats[c]:
            cats[c][s] = []
            sub_order[c].append(s)
        cats[c][s].append(
            {
                "title": e["title"],
                "file": e["file"],
                "description": e["description"],
                "added": e["added"],
            }
        )

    # Light ordering: Uncategorized always last; within category, _default first.
    def cat_key(name: str) -> tuple:
        return (1 if name == "Uncategorized" else 0, name.lower())

    cat_order.sort(key=cat_key)
    for c in cat_order:
        sub_order[c].sort(key=lambda s: (0 if s == "_default" else 1, s.lower()))

    return [
        {
            "name": c,
            "subcategories": [
                {
                    "name": s,
                    "items": sorted(
                        cats[c][s], key=lambda it: (it["added"], it["title"].lower()), reverse=True
                    ),
                }
                for s in sub_order[c]
            ],
        }
        for c in cat_order
    ]


def build_manifest() -> dict:
    overrides = load_overrides()

    html_files = sorted(
        p for p in ROOT.glob("*.html") if p.name.lower() != "index.html"
    )
    if not html_files:
        print("  (no HTML files found — the library will be empty)")
    entries = [build_entry(p, overrides) for p in html_files]
    categories = group(entries)

    return {
        "generated": _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "categories": categories,
    }


def rewrite_index(manifest: dict) -> None:
    if not INDEX.exists():
        print(f"ERROR: {INDEX.name} is missing. Put this script next to it.", file=sys.stderr)
        sys.exit(1)

    text = INDEX.read_text(encoding="utf-8")
    start = text.find(MARK_START)
    end = text.find(MARK_END, start + len(MARK_START) if start != -1 else 0)
    if start == -1 or end == -1:
        print(
            f"ERROR: could not find the manifest markers in {INDEX.name}.\n"
            f"Make sure these two lines exist:\n    {MARK_START}\n    {MARK_END}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Indent the manifest for readability inside the file.
    body = json.dumps(manifest, indent=2, ensure_ascii=False)
    new_block = (
        f"{MARK_START}\n"
        f"window.__MANIFEST__ = {body};\n"
    )

    new_text = text[:start] + new_block + text[end:]
    INDEX.write_text(new_text, encoding="utf-8")


def main() -> None:
    manifest = build_manifest()
    rewrite_index(manifest)
    total = sum(
        len(s["items"]) for c in manifest["categories"] for s in c["subcategories"]
    )
    print(f"✓ Wrote {total} piece(s) across {len(manifest['categories'])} "
          f"categor{'y' if len(manifest['categories']) == 1 else 'ies'} into {INDEX.name}.")
    for c in manifest["categories"]:
        print(f"  • {c['name']}")
        for s in c["subcategories"]:
            label = "" if s["name"] == "_default" else f" / {s['name']}"
            for it in s["items"]:
                print(f"      – {it['title']}{label}  [{it['file']}]")


if __name__ == "__main__":
    main()
