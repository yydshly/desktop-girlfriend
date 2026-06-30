from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
LAYER_DIR = ROOT / "assets" / "avatar" / "layers"
MANIFEST = LAYER_DIR / "manifest.json"


def transparent(size: tuple[int, int]) -> Image.Image:
    return Image.new("RGBA", size, (0, 0, 0, 0))


def save_layer(name: str, image: Image.Image) -> None:
    image.save(LAYER_DIR / name)


def draw_shadow(size: tuple[int, int]) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    draw.ellipse((270, 1370, 754, 1488), fill=(0, 0, 0, 96))
    return image.filter(ImageFilter.GaussianBlur(18))


def draw_hair_back(size: tuple[int, int]) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    draw.ellipse((292, 180, 732, 730), fill=(86, 45, 36, 255))
    draw.rounded_rectangle((292, 360, 438, 1040), radius=80, fill=(82, 42, 34, 245))
    draw.rounded_rectangle((586, 360, 732, 1040), radius=80, fill=(82, 42, 34, 245))
    return image.filter(ImageFilter.GaussianBlur(0.4))


def draw_base_body(size: tuple[int, int]) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)

    draw.ellipse((344, 190, 680, 528), fill=(255, 220, 207, 255))
    draw.pieslice((360, 160, 664, 440), 180, 360, fill=(105, 58, 45, 255))
    draw.rounded_rectangle((385, 500, 640, 960), radius=86, fill=(255, 196, 212, 255))
    draw.polygon([(384, 900), (640, 900), (720, 1110), (304, 1110)], fill=(238, 241, 252, 255))

    draw.rounded_rectangle((300, 540, 410, 900), radius=50, fill=(255, 196, 212, 255))
    draw.rounded_rectangle((614, 540, 724, 900), radius=50, fill=(255, 196, 212, 255))
    draw.ellipse((292, 860, 410, 980), fill=(255, 220, 207, 255))
    draw.ellipse((614, 860, 732, 980), fill=(255, 220, 207, 255))

    draw.rounded_rectangle((380, 1080, 468, 1390), radius=42, fill=(255, 220, 207, 255))
    draw.rounded_rectangle((556, 1080, 644, 1390), radius=42, fill=(255, 220, 207, 255))
    draw.rounded_rectangle((352, 1370, 480, 1430), radius=28, fill=(244, 245, 250, 255))
    draw.rounded_rectangle((544, 1370, 672, 1430), radius=28, fill=(244, 245, 250, 255))

    draw.line((512, 500, 512, 940), fill=(232, 154, 176, 110), width=4)
    draw.line((486, 526, 538, 526), fill=(255, 250, 248, 210), width=14)
    draw.line((512, 526, 486, 588), fill=(160, 67, 75, 210), width=8)
    draw.line((512, 526, 540, 588), fill=(160, 67, 75, 210), width=8)
    return image


def draw_eye_white(size: tuple[int, int], side: str) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    box = (414, 338, 484, 384) if side == "left" else (540, 338, 610, 384)
    draw.ellipse(box, fill=(255, 248, 244, 255))
    draw.arc(box, 190, 350, fill=(72, 38, 36, 210), width=5)
    return image


def draw_pupil(size: tuple[int, int], side: str) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    box = (438, 346, 464, 374) if side == "left" else (564, 346, 590, 374)
    draw.ellipse(box, fill=(74, 42, 48, 255))
    draw.ellipse((box[0] + 8, box[1] + 5, box[0] + 14, box[1] + 11), fill=(255, 255, 255, 230))
    return image


def draw_mouth(size: tuple[int, int], shape: str) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    boxes = {
        "closed": (488, 426, 536, 434),
        "small": (490, 420, 534, 444),
        "medium": (486, 414, 538, 458),
        "large": (482, 408, 542, 474),
    }
    box = boxes[shape]
    if shape == "closed":
        draw.arc(box, 0, 180, fill=(126, 45, 67, 255), width=5)
    else:
        draw.ellipse(box, fill=(112, 34, 60, 255))
        draw.arc((box[0] + 5, box[1] + 4, box[2] - 5, box[3] - 6), 20, 160, fill=(250, 128, 144, 170), width=4)
    return image


def draw_eyelid(size: tuple[int, int], side: str) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    box = (410, 334, 488, 388) if side == "left" else (536, 334, 614, 388)
    draw.ellipse(box, fill=(255, 220, 207, 245))
    draw.arc(box, 190, 350, fill=(100, 55, 50, 210), width=5)
    return image


def draw_hair_front(size: tuple[int, int]) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    draw.polygon([(356, 230), (424, 170), (496, 328), (440, 332)], fill=(112, 64, 50, 255))
    draw.polygon([(454, 184), (518, 162), (542, 334), (488, 326)], fill=(101, 55, 43, 255))
    draw.polygon([(548, 176), (664, 238), (596, 338), (538, 328)], fill=(112, 64, 50, 255))
    return image


def draw_blush(size: tuple[int, int]) -> Image.Image:
    image = transparent(size)
    draw = ImageDraw.Draw(image)
    draw.ellipse((372, 392, 438, 428), fill=(255, 130, 154, 72))
    draw.ellipse((586, 392, 652, 428), fill=(255, 130, 154, 72))
    return image.filter(ImageFilter.GaussianBlur(8))


def main() -> int:
    LAYER_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    size = (manifest["canvas"]["width"], manifest["canvas"]["height"])

    layers = {
        "shadow.png": draw_shadow(size),
        "hair-back.png": draw_hair_back(size),
        "base-body.png": draw_base_body(size),
        "eye-left-white.png": draw_eye_white(size, "left"),
        "eye-right-white.png": draw_eye_white(size, "right"),
        "pupil-left.png": draw_pupil(size, "left"),
        "pupil-right.png": draw_pupil(size, "right"),
        "mouth-closed.png": draw_mouth(size, "closed"),
        "mouth-small.png": draw_mouth(size, "small"),
        "mouth-medium.png": draw_mouth(size, "medium"),
        "mouth-large.png": draw_mouth(size, "large"),
        "eyelid-left.png": draw_eyelid(size, "left"),
        "eyelid-right.png": draw_eyelid(size, "right"),
        "hair-front.png": draw_hair_front(size),
        "blush.png": draw_blush(size),
    }

    for file_name, image in layers.items():
        save_layer(file_name, image)
        print(f"wrote assets/avatar/layers/{file_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
