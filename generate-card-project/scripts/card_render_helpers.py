"""Reusable helpers for dense Chinese card rendering and AI illustration cleanup."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def measure_text(font: ImageFont.ImageFont, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for ch in paragraph:
            test = current + ch
            width, _ = measure_text(font, test)
            if width > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def detect_text_in_image(image_path: str | Path) -> float:
    """Return a heuristic text-suspicion score; higher means more likely to contain text."""
    img = Image.open(image_path).convert("L").resize((512, 384))
    arr = np.array(img, dtype=np.int16)
    rows, cols = 16, 12
    ch, cw = arr.shape[0] // rows, arr.shape[1] // cols
    bg_bright = float(np.percentile(arr, 60))
    suspicious_cells = 0

    for r in range(rows):
        for c in range(cols):
            cell = arr[r * ch : (r + 1) * ch, c * cw : (c + 1) * cw]
            if bg_bright - float(cell.mean()) < 25:
                continue
            dark_ratio = float(np.sum(cell < 100)) / cell.size
            if 0.10 < dark_ratio < 0.55:
                v_diff = np.abs(cell[:, 2:] - cell[:, :-2])
                edge_density = float(np.sum(v_diff > 40)) / v_diff.size
                if edge_density > 0.04:
                    suspicious_cells += 1

    return round(suspicious_cells / (rows * cols) * 100, 1)


def make_irregular_alpha_mask(width: int, height: int, blur_radius: int = 2) -> Image.Image:
    """Create a feathered alpha mask with independently rounded irregular corners."""
    min_side = min(width, height)
    radii = [int(min_side * random.uniform(0.30, 0.45)) for _ in range(4)]
    fade_dists = [int(radius * random.uniform(0.25, 0.35)) for radius in radii]
    r_tl, r_tr, r_bl, r_br = radii

    yy = np.linspace(0, height - 1, height)[:, np.newaxis]
    xx = np.linspace(0, width - 1, width)[np.newaxis, :]
    alpha = np.ones((height, width), dtype=np.float32)

    corners = [
        (r_tl, r_tl, r_tl, xx < r_tl, yy < r_tl, fade_dists[0]),
        (width - r_tr, r_tr, r_tr, xx > width - r_tr, yy < r_tr, fade_dists[1]),
        (r_bl, height - r_bl, r_bl, xx < r_bl, yy > height - r_bl, fade_dists[2]),
        (width - r_br, height - r_br, r_br, xx > width - r_br, yy > height - r_br, fade_dists[3]),
    ]

    for cx, cy, radius, x_mask, y_mask, fade_dist in corners:
        in_bbox = x_mask & y_mask
        if not np.any(in_bbox):
            continue
        dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        signed = dist - radius
        alpha[in_bbox & (signed > fade_dist)] = 0.0
        in_transition = in_bbox & (signed > 0) & (signed <= fade_dist)
        t = np.clip(signed[in_transition] / fade_dist, 0.0, 1.0)
        alpha[in_transition] = 1.0 - t

    mask = Image.fromarray((alpha * 255).astype(np.uint8))
    return mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))


def blend_to_paper_tone(
    image: Image.Image,
    paper_rgb: tuple[int, int, int] = (245, 235, 210),
    image_weight: float = 0.82,
) -> Image.Image:
    arr = np.array(image.convert("RGB"), dtype=np.float32)
    bg_arr = np.array(paper_rgb, dtype=np.float32).reshape(1, 1, 3)
    arr = arr * image_weight + bg_arr * (1.0 - image_weight)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def prepare_illustration_for_composite(
    image_path: str | Path,
    target_size: tuple[int, int],
    paper_rgb: tuple[int, int, int] = (245, 235, 210),
) -> tuple[Image.Image, Image.Image]:
    img = Image.open(image_path).convert("RGB").resize(target_size, Image.Resampling.LANCZOS)
    img = blend_to_paper_tone(img, paper_rgb=paper_rgb)
    mask = make_irregular_alpha_mask(*target_size)
    return img, mask


def draw_wrapped_lines(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    line_gap: int,
    paragraph_gap: int,
) -> int:
    x, y = xy
    _, line_h = measure_text(font, "测试")
    for line in lines:
        if line:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_h + line_gap
        else:
            y += paragraph_gap
    return y
