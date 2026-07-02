from __future__ import annotations

import base64
import os
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from flask import Flask, render_template, request, send_from_directory
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from scripts.card_render_helpers import measure_text, wrap_text
from scripts.parse_idiom_markdown import make_pinyin

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output_cards"
ILLUSTRATION_DIR = OUTPUT_DIR / "illustrations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ILLUSTRATION_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in names:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def build_prompt_content(idiom: str, pinyin: str, explanation: str, story: str, tip: str) -> dict[str, str]:
    return {
        "idiom": idiom,
        "pinyin": pinyin or make_pinyin(idiom) or "",
        "explanation": explanation or f"{idiom}是一个富有教育意义的成语，适合用来培养观察力与表达能力。",
        "story": story or f"这个成语故事可以通过生活中的小例子帮助孩子理解其含义。",
        "tip": tip or f"在教学中，可以结合日常情境让孩子更好地理解{idiom}。",
    }


def call_normal_model(idiom: str, base_url: str, api_key: str, model_name: str) -> dict[str, str]:
    if not base_url or not api_key:
        return build_prompt_content(idiom, "", "", "", "")

    prompt = (
        "你是一位中文教育内容策划师。请用简洁、适合儿童阅读的中文，生成一个成语卡片的三个部分："
        f"成语：{idiom}\n"
        "1. 简单解释：二到三句，通俗易懂；"
        "2. 故事讲述：一个短小故事；"
        "3. 家长提示：一条教育建议。"
        "请以 JSON 格式返回 {\"explanation\":..., \"story\":..., \"tip\":...}"
    )
    payload = {
        "model": model_name or "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个中文教育内容生成器，输出必须是 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = f"{base_url.rstrip('/')}/chat/completions"
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    content = re.sub(r"```json|```", "", content).strip()
    try:
        parsed = eval(content, {"__builtins__": {}}, {})
    except Exception:
        parsed = {}
    if isinstance(parsed, dict):
        return {
            "idiom": idiom,
            "pinyin": make_pinyin(idiom) or "",
            "explanation": normalize_text(parsed.get("explanation")) or build_prompt_content(idiom, "", "", "", "")["explanation"],
            "story": normalize_text(parsed.get("story")) or build_prompt_content(idiom, "", "", "", "")["story"],
            "tip": normalize_text(parsed.get("tip")) or build_prompt_content(idiom, "", "", "", "")["tip"],
        }
    return build_prompt_content(idiom, "", "", "", "")


def create_placeholder_illustration(output_path: Path) -> Path:
    img = Image.new("RGB", (1024, 1024), (245, 235, 210))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((70, 70, 954, 954), radius=60, outline=(170, 135, 95), width=14)
    draw.rectangle((110, 240, 914, 800), fill=(255, 248, 233), outline=(210, 180, 120), width=6)
    draw.text((512, 430), "成语故事", fill=(95, 65, 35), anchor="mm", font=get_font(44))
    draw.text((512, 560), "AI 生图可替换插图", fill=(125, 95, 60), anchor="mm", font=get_font(28))
    img.save(output_path)
    return output_path


def call_image_model(prompt: str, base_url: str, api_key: str, model_name: str, output_path: Path) -> Path:
    if not base_url or not api_key:
        return create_placeholder_illustration(output_path)

    payload = {
        "model": model_name or "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1024",
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = f"{base_url.rstrip('/')}/images/generations"
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    image_b64 = None
    if data.get("data") and data["data"][0].get("b64_json"):
        image_b64 = data["data"][0]["b64_json"]
    elif data.get("data") and data["data"][0].get("url"):
        image_url = data["data"][0]["url"]
        img_resp = requests.get(image_url, timeout=60)
        img_resp.raise_for_status()
        output_path.write_bytes(img_resp.content)
        return output_path

    if image_b64:
        image_bytes = base64.b64decode(image_b64)
        output_path.write_bytes(image_bytes)
        return output_path

    return create_placeholder_illustration(output_path)


def generate_card(card: dict[str, str], illustration_path: Path, output_path: Path) -> Path:
    W, H = 1530, 2741
    base = Image.new("RGB", (W, H), (248, 236, 210))
    draw = ImageDraw.Draw(base)

    draw.rounded_rectangle((40, 40, W - 40, H - 40), radius=42, outline=(178, 146, 102), width=7)
    draw.rounded_rectangle((60, 60, W - 60, H - 60), radius=38, outline=(216, 191, 150), width=3)

    title_font = get_font(int(W * 0.065))
    pinyin_font = get_font(int(W * 0.03))
    label_font = get_font(int(W * 0.038))
    body_font = get_font(int(W * 0.032))

    draw.text((W // 2, int(H * 0.06)), card["idiom"], fill=(108, 74, 39), anchor="ma", font=title_font)

    pinyin = card.get("pinyin", "")
    if pinyin:
        parts = pinyin.split()
        char_count = min(len(parts), 5)
        cell_width = int(W * 0.16) if char_count <= 4 else int(W * 0.13)
        start_x = int(W * 0.23)
        for idx in range(char_count):
            cell_x = start_x + idx * cell_width
            cell_center_x = cell_x + cell_width // 2
            pw, _ = measure_text(pinyin_font, parts[idx])
            draw.text((cell_center_x - pw // 2, int(H * 0.11)), parts[idx], fill=(140, 110, 90), font=pinyin_font)

    if illustration_path.exists():
        illustration = Image.open(illustration_path).convert("RGB")
        illustration = illustration.resize((int(W * 0.8), int(H * 0.34)), Image.Resampling.LANCZOS)
        illustration = ImageOps.contain(illustration, (int(W * 0.8), int(H * 0.34)))
        x = int(W * 0.1)
        y = int(H * 0.16)
        mask = Image.new("L", illustration.size, 255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius=8))
        base.paste(illustration, (x, y), mask)

    sections = [
        ("简单解释", card.get("explanation", "")),
        ("故事讲述", card.get("story", "")),
        ("家长提示", card.get("tip", "")),
    ]

    y = int(H * 0.58)
    for label, content in sections:
        draw.text((int(W * 0.10), y), label, fill=(132, 92, 44), font=label_font)
        y += int(H * 0.04)
        lines = wrap_text(content, body_font, int(W * 0.8))
        for line in lines:
            if line:
                draw.text((int(W * 0.10), y), line, fill=(80, 62, 42), font=body_font)
                y += int(H * 0.035)
            else:
                y += int(H * 0.018)
        y += int(H * 0.02)

    draw.text((W - int(W * 0.12), H - int(H * 0.08)), card.get("series_number", "E01/001"), fill=(120, 100, 80), font=pinyin_font)
    base.save(output_path)
    return output_path


@app.get("/")
def index():
    return render_template("index.html", result=None, error=None)


@app.post("/generate")
def generate():
    idiom = normalize_text(request.form.get("idiom"))
    pinyin = normalize_text(request.form.get("pinyin"))
    explanation = normalize_text(request.form.get("explanation"))
    story = normalize_text(request.form.get("story"))
    tip = normalize_text(request.form.get("tip"))

    if not idiom:
        return render_template("index.html", result=None, error="请输入成语名称")

    normal_base = normalize_text(request.form.get("normal_base")) or os.getenv("NORMAL_API_BASE", "")
    normal_key = normalize_text(request.form.get("normal_key")) or os.getenv("NORMAL_API_KEY", "")
    normal_model = normalize_text(request.form.get("normal_model")) or os.getenv("NORMAL_MODEL", "gpt-4o-mini")
    image_base = normalize_text(request.form.get("image_base")) or os.getenv("IMAGE_API_BASE", "")
    image_key = normalize_text(request.form.get("image_key")) or os.getenv("IMAGE_API_KEY", "")
    image_model = normalize_text(request.form.get("image_model")) or os.getenv("IMAGE_MODEL", "gpt-image-1")

    card = build_prompt_content(idiom, pinyin, explanation, story, tip)
    try:
        if normal_base and normal_key:
            card = call_normal_model(idiom, normal_base, normal_key, normal_model)
        else:
            card["pinyin"] = pinyin or make_pinyin(idiom) or ""
            card["explanation"] = explanation or card["explanation"]
            card["story"] = story or card["story"]
            card["tip"] = tip or card["tip"]
    except Exception as exc:
        card = build_prompt_content(idiom, pinyin, explanation, story, tip)
        card["explanation"] = explanation or card["explanation"]
        card["story"] = story or card["story"]
        card["tip"] = tip or card["tip"]
        error = f"正常模型调用失败：{exc}，已改用本地默认内容。"
    else:
        error = None

    card["series_number"] = f"E01/{uuid.uuid4().hex[:4].upper()}"
    image_name = re.sub(r"[^\w]+", "_", idiom).strip("_") or "idiom"
    illustration_path = ILLUSTRATION_DIR / f"{image_name}_illustration.png"
    output_path = OUTPUT_DIR / f"{image_name}.png"

    try:
        if image_base and image_key:
            call_image_model(
                (
                    "中国古风插画，成语教育卡片背景，色调温暖，古典场景，适合儿童阅读，"
                    f"与{idiom}相关的故事氛围，禁止文字、禁止字样、禁止标志"
                ),
                image_base,
                image_key,
                image_model,
                illustration_path,
            )
        else:
            create_placeholder_illustration(illustration_path)
    except Exception:
        create_placeholder_illustration(illustration_path)

    generate_card(card, illustration_path, output_path)
    image_url = f"/output/{output_path.name}"
    return render_template("index.html", result={"card": card, "image_url": image_url, "output_path": output_path.name}, error=error)


@app.get("/output/<path:filename>")
def output_file(filename: str):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
