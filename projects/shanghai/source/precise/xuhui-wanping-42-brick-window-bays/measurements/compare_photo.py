"""Crop the street photograph to the registered GLB projection and credit its author."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def comparison(original, rendered, out):
    frame = Image.open(rendered).convert("RGB")
    with Image.open(original) as photo:
        # The camera fit and the crop in render_street.py use this working raster.
        reference = photo.convert("RGB").resize((1050, 788), Image.Resampling.LANCZOS)
    reference = reference.crop((234, 0, 902, 787)).resize(frame.size, Image.Resampling.LANCZOS)
    width, height = frame.size
    margin = 22
    canvas = Image.new("RGB", (2 * width + 3 * margin, height + 150), (247, 245, 240))
    draw = ImageDraw.Draw(canvas)
    family = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    heading = ImageFont.truetype(family, 27)
    label = ImageFont.truetype(family, 18)
    small = ImageFont.truetype(family, 15)
    draw.text((margin, 6), "宛平路42号住宅  ·  双色砖墙与卷叶凸窗", font=heading, fill="#292824")
    canvas.paste(reference, (margin, 52))
    canvas.paste(frame, (2 * margin + width, 52))
    draw.text((margin, height + 62), "Livelikerw 摄于2019年2月23日，照片经裁切。", font=label, fill="#363531")
    draw.text((2 * margin + width, height + 62),
              "按同一视角渲染的四座凸窗、浮雕门楣和楼顶格窗。", font=label, fill="#363531")
    draw.text((margin, height + 96), "原图  commons.wikimedia.org/wiki/File:42_Wanping_Road.jpg", font=small, fill="#45433f")
    draw.text((2 * margin + width, height + 96),
              "此对照图采用 CC BY-SA 4.0  ·  creativecommons.org/licenses/by-sa/4.0", font=small, fill="#45433f")
    canvas.save(out, quality=91, optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("rendered", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    comparison(args.original, args.rendered, args.output)
