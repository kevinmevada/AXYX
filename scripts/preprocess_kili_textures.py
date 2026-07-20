"""Downscale KILI TGA textures to runtime PNG cache (no ufbx)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
KILI = ROOT / "KILI"
CACHE = KILI / "cache" / "textures"

MAPPING = [
    ("T_Body_BC_VT.TGA", "body_bc.png", 2048),
    ("T_Body_N_VT.TGA", "body_n.png", 2048),
    ("T_Body_SRMF_VT.TGA", "body_srmf.png", 2048),
    ("T_Body_Scatter_VT.TGA", "body_scatter.png", 1024),
]


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    out = []
    for src_name, dst_name, max_dim in MAPPING:
        src = KILI / src_name
        if not src.is_file():
            print(f"skip missing {src_name}")
            continue
        print(f"Loading {src_name}…", flush=True)
        img = Image.open(src)
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
        w, h = img.size
        scale = min(1.0, max_dim / float(max(w, h)))
        if scale < 1.0:
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.Resampling.LANCZOS,
            )
        dst = CACHE / dst_name
        img.save(dst, optimize=True)
        out.append(
            {
                "source": src_name,
                "cache": str(dst.relative_to(ROOT)).replace("\\", "/"),
                "size": list(img.size),
            }
        )
        print(f"  -> {dst.name} {img.size}", flush=True)
    (KILI / "cache" / "textures.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print("Done")


if __name__ == "__main__":
    main()
