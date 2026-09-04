#!/usr/bin/env python3
"""
Bake the live salt-lighting.vercel.app product renders into the brochure.

The brochure currently loads twelve renders from the live site and falls back
to lower-resolution renders embedded in the file when it can't reach the
network. Run this once on a machine with internet access and the high-quality
renders get embedded too, so the file is fully self-contained again.

    pip install requests pillow
    python3 embed-live-images.py

Writes SALT-Interactive-Brochure-embedded.html next to the original.
Re-runnable and non-destructive: the input file is never modified.
"""

import base64
import io
import json
import pathlib
import re
import sys

try:
    import requests
    from PIL import Image
except ImportError:
    sys.exit("Missing dependencies. Run:  pip install requests pillow")

SRC = pathlib.Path(__file__).with_name("index.html")
OUT = pathlib.Path(__file__).with_name("index.embedded.html")

# Longest edge of the baked-in render. 1400 keeps the datasheet hero crisp on a
# retina display without bloating the file; drop to 900 for a leaner document.
MAX_EDGE = 1400
WEBP_QUALITY = 82

# Match the plate tone the PDF-derived renders were normalised to, so the
# collection grid stays visually even.
PLATE = 244


def normalise(img):
    """Lift the studio backdrop to the shared plate tone."""
    from PIL import ImageStat
    w, h = img.size
    corners = [
        img.crop((0, 0, w // 12, h // 12)),
        img.crop((w - w // 12, 0, w, h // 12)),
        img.crop((0, h - h // 12, w // 12, h)),
        img.crop((w - w // 12, h - h // 12, w, h)),
    ]
    means = [ImageStat.Stat(c).mean[:3] for c in corners]
    bg = sorted(means, key=lambda m: -sum(m))[0]
    lum = sum(bg) / 3
    if 150 < lum < 250:
        f = PLATE / lum
        img = img.point(lambda p, f=f: min(255, int(p * f)))
    return img


def main():
    if not SRC.exists():
        sys.exit(f"Can't find {SRC.name} next to this script.")

    html = SRC.read_text(encoding="utf-8")
    i = html.index("const P = [")
    j = html.index("];\nconst FAMS")
    products = json.loads(html[i + len("const P = "): j + 1])

    targets = [p for p in products if p.get("liveHi") or p.get("live")]
    print(f"{len(targets)} products reference a live render.\n")

    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (SALT brochure image embedder)"

    ok = failed = 0
    for p in targets:
        url = p.get("liveHi") or p["live"]
        try:
            r = session.get(url, timeout=45)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            src_size = img.size
            img = normalise(img)
            img.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, "WEBP", quality=WEBP_QUALITY, method=5)
            p["img"] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
            # the live URLs are no longer needed; keep src_url as provenance
            p.pop("live", None)
            p.pop("liveHi", None)
            kb = len(buf.getvalue()) // 1024
            print(f"  ✓ {p['name']:<18} {src_size[0]}×{src_size[1]} → {img.size[0]}×{img.size[1]}  {kb} KB")
            ok += 1
        except Exception as exc:
            print(f"  ✗ {p['name']:<18} {type(exc).__name__}: {exc}")
            print(f"      keeping the embedded fallback render")
            failed += 1

    payload = json.dumps(products, ensure_ascii=False, separators=(",", ":"))
    html = html[:i] + "const P = " + payload + html[j + 1:]
    OUT.write_text(html, encoding="utf-8")

    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"\n{ok} embedded, {failed} kept as fallback.")
    print(f"Wrote {OUT.name} — {size_mb:.2f} MB, no network required.")


if __name__ == "__main__":
    main()
