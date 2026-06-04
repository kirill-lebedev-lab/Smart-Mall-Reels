#!/usr/bin/env python3
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = PROJECT_ROOT / "images/navigation/001-008.png"
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
TEXT_COLOR = "0xFFF6DC"

THUMBNAILS = {
    "en": {
        "title": "SMART MALL",
        "subtitle": "Space that responds to people",
        "output": PROJECT_ROOT / "output/thumbnail_navigation_en.png",
    },
    "ru": {
        "title": "УМНЫЙ МОЛЛ",
        "subtitle": "Пространство, которое\nреагирует на людей",
        "output": PROJECT_ROOT / "output/thumbnail_navigation_ru.png",
    },
}

FONT_CANDIDATES = [
    (Path("/System/Library/Fonts/Avenir Next.ttc"), 5),
    (Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"), 0),
    (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), 0),
]


def load_font(candidates: list[tuple[Path, int]], size: int) -> ImageFont.FreeTypeFont:
    for path, index in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size, index=index)
    raise FileNotFoundError("No suitable thumbnail font was found.")


def crop_for_thumbnail(image: Image.Image) -> Image.Image:
    # Keep the visitor and the complete interactive display in the vertical crop.
    crop_width = round(image.height * OUTPUT_WIDTH / OUTPUT_HEIGHT)
    left = min(max(0, 375), image.width - crop_width)
    cropped = image.crop((left, 0, left + crop_width, image.height))
    return cropped.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT), Image.Resampling.LANCZOS)


def apply_poster_treatment(image: Image.Image) -> Image.Image:
    image = ImageEnhance.Contrast(image).enhance(1.04)
    image = ImageEnhance.Color(image).enhance(1.03)
    image = ImageEnhance.Brightness(image).enhance(1.04)

    warm_overlay = Image.new("RGB", image.size, (255, 179, 92))
    image = Image.blend(image, warm_overlay, 0.015)

    vignette = ImageOps.invert(Image.radial_gradient("L")).resize(image.size)
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    vignette = vignette.point(lambda value: int(value * 0.09))
    return Image.composite(Image.new("RGB", image.size, (6, 5, 4)), image, vignette)


def add_local_text_backdrop(image: Image.Image) -> Image.Image:
    backdrop = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(backdrop)
    draw.rounded_rectangle((350, 1480, 1120, 1840), radius=52, fill=(4, 5, 6, 48))
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(42))
    return Image.alpha_composite(image.convert("RGBA"), backdrop).convert("RGB")


def draw_thumbnail_text(image: Image.Image, title: str, subtitle: str) -> None:
    title_font = load_font(FONT_CANDIDATES, 72)
    subtitle_font = load_font(FONT_CANDIDATES, 40)
    x = 390
    title_y = 1545
    subtitle_y = 1650
    text_color = tuple(bytes.fromhex(TEXT_COLOR.removeprefix("0x")))

    text_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    draw.text((x + 2, title_y + 3), title, font=title_font, fill=(0, 0, 0, 105))
    draw.text((x, title_y), title, font=title_font, fill=(*text_color, 255))
    draw.multiline_text(
        (x + 2, subtitle_y + 2),
        subtitle,
        font=subtitle_font,
        fill=(0, 0, 0, 95),
        spacing=8,
    )
    draw.multiline_text(
        (x, subtitle_y),
        subtitle,
        font=subtitle_font,
        fill=(*text_color, 255),
        spacing=8,
    )
    image.paste(Image.alpha_composite(image.convert("RGBA"), text_layer).convert("RGB"))


def generate_thumbnail(title: str, subtitle: str, output_path: Path) -> None:
    if not SOURCE_IMAGE.exists():
        raise FileNotFoundError(f"Missing thumbnail source image: {SOURCE_IMAGE}")

    with Image.open(SOURCE_IMAGE) as source:
        image = crop_for_thumbnail(source.convert("RGB"))
    image = apply_poster_treatment(image)
    image = add_local_text_backdrop(image)
    draw_thumbnail_text(image, title, subtitle)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, "PNG", optimize=True)


def generate_thumbnails() -> dict[str, Path]:
    outputs = {}
    for language, settings in THUMBNAILS.items():
        output_path = settings["output"]
        generate_thumbnail(settings["title"], settings["subtitle"], output_path)
        outputs[language] = output_path
        print(f"Thumbnail created: {output_path.resolve()}")
    return outputs


def main() -> int:
    try:
        generate_thumbnails()
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
