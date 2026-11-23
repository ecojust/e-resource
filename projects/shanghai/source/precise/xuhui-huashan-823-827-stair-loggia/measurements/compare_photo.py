"""Crop the street photograph to the registered GLB projection and credit its author."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def comparison(original, rendered, out):
    frame = Image.open(rendered).convert("RGB")
    with Image.open(original) as photo:
        # The camera fit and the crop in render_loggia.py use this working raster.
        reference = photo.convert("RGB").resize((1300, 731), Image.Resampling.LANCZOS)
    reference = reference.crop((42, 5, 1240, 699)).resize(frame.size, Image.Resampling.LANCZOS)
    width, height = frame.size
    margin = 22
    canvas = Image.new("RGB", (2 * width + 3 * margin, height + 150), (247, 245, 240))
    draw = ImageDraw.Draw(canvas)
    family = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    heading = ImageFont.truetype(family, 27)
    label = ImageFont.truetype(family, 18)
    small = ImageFont.truetype(family, 15)
    draw.text((margin, 6), "华山路823、825、827号院  ·  临街三山墙住宅", font=heading, fill="#292824")
    canvas.paste(reference, (margin, 52))
    canvas.paste(frame, (2 * margin + width, 52))
    draw.text((margin, height + 62), "Antigng 摄于2018年2月10日，照片经裁切。", font=label, fill="#363531")
    draw.text((2 * margin + width, height + 62),
              "按拍摄位置渲染。两翼的灰色抹面、花砖和拱厅均来自模型。", font=label, fill="#363531")
    draw.text((margin, height + 96), "原图  commons.wikimedia.org/wiki/File:华山路823号住宅.jpg", font=small, fill="#45433f")
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
