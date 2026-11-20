#!/usr/bin/env python3
"""Extract per-slide text from a PowerPoint `.pptx` deck (stdlib only).

A `.pptx` is a zip archive. Slide text lives in `ppt/slides/slideN.xml` as
`<a:t ...>...</a:t>` runs (the tag usually carries `xml:space="preserve"`, which
is why the matcher allows attributes). This script reads those runs in true
slide-display order (via `ppt/presentation.xml` + its rels) and prints
`Slide N: <text>` per slide, so the output can drive accurate page-by-page
accounting even when no slide renderer (LibreOffice / soffice) is installed.

The slide count it reports equals the number of slides in the deck, which is the
number you must reconcile against in the Source Page-Map.

Usage:
    python3 extract_pptx.py deck.pptx [output_txt]
"""
import sys
import re
import zipfile

# Match <a:t ...>...</a:t> (allow attributes such as xml:space="preserve").
# The `\b` after `t` is essential: without it `<a:t[^>]*>` would also match
# `<a:tbl>`, `<a:tblPr>`, `<a:tblGrid>` etc. (they start with `<a:t`) and
# swallow the whole shape/table XML until the next real `</a:t>`.
RUN_RE = re.compile(r'<a:t\b[^>]*>(.*?)</a:t>', re.DOTALL)


def _order_from_presentation(zf):
    """Return slide xml zip-paths in display order, or None if undeterminable."""
    try:
        xml = zf.read('ppt/presentation.xml').decode('utf-8', 'ignore')
    except KeyError:
        return None
    rids = re.findall(r'<p:sldId[^>]*\br:id="([^"]+)"', xml)
    if not rids:
        return None
    try:
        rels = zf.read('ppt/_rels/presentation.xml.rels').decode('utf-8', 'ignore')
    except KeyError:
        return None
    rid_to_target = dict(
        re.findall(r'<Relationship\b[^>]*\bId="([^"]+)"[^>]*Target="([^"]+)"', rels)
    )
    paths = []
    for rid in rids:
        tgt = rid_to_target.get(rid)
        if not tgt:
            continue
        # rels Target is relative to ppt/_rels/, i.e. relative to ppt/.
        if not tgt.startswith('ppt/'):
            tgt = 'ppt/' + tgt.lstrip('/')
        paths.append(tgt)
    return paths or None


def slide_text(zf, path):
    try:
        xml = zf.read(path).decode('utf-8', 'ignore')
    except KeyError:
        return ''
    runs = RUN_RE.findall(xml)
    txt = ' '.join(re.sub(r'\s+', ' ', r).strip() for r in runs if r.strip())
    return txt.strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: extract_pptx.py <deck.pptx> [output_txt]")
        sys.exit(1)
    deck = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None

    with zipfile.ZipFile(deck) as zf:
        order = _order_from_presentation(zf)
        if order is None:
            # Fallback: any slideN.xml, sorted numerically.
            order = sorted(
                [n for n in zf.namelist() if re.match(r'ppt/slides/slide\d+\.xml$', n)],
                key=lambda n: int(re.search(r'(\d+)', n).group(1)),
            )

        lines = []
        lines.append(f"# Slide text: {deck}")
        lines.append(f"- Slides: {len(order)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        for i, path in enumerate(order, 1):
            lines.append(f"\n**Slide {i}** (`{path}`)")
            lines.append(slide_text(zf, path) or "(blank)")

    md = "\n".join(lines)
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"Wrote {out} ({len(md)} chars, {len(order)} slides)", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()
