"""Draw the dated Changzhi Road street openings from a complete released model."""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'jingan-bank-of-communications-warehouse-guangfu-riverfront/measurements'))
from render_riverfront_survey import load_raster, raster
from check_street_entrances import cameras


def board(mesh, output):
    canvas = Image.new('RGB', (1280, 902), '#f4f1ea')
    draw = ImageDraw.Draw(canvas)
    def text(x, y, content, pts=21, bold=False):
        style = 'Bold' if bold else 'Regular'
        font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-' + style + '.ttc', pts, index=2)
        draw.text((x, y), content, font=font, fill='#233033')
    text(35, 14, '同仁医院旧址 · 长治路底层门廊与山花下窗洞', 35, True)
    text(36, 73, '图中均为成品模型。三处取景沿用照片或街景的机位，墙面按2023年区刊所见状态绘制。', 19)
    views = [
        ('street_2021', [520, 280, 1050, 521], 728, (36,129)),
        ('fayhoo_2016_gable', [1480,940,1724,1233], 402, (842,129)),
        ('district_2023', [16,964,414,1088], 728, (36,550))]
    lamp = np.array([-.75, -.45, .62])
    lamp /= np.linalg.norm(lamp)
    proof = {}
    with tempfile.TemporaryDirectory() as tmp:
        lib = load_raster(tmp)
        for name, crop, width, pos in views:
            image, stats = raster(mesh, lib, width*2, cameras()[name], crop, lamp, (239,35))
            image = image.resize((width, round(image.height/2)), Image.Resampling.LANCZOS)
            canvas.paste(image, pos)
            proof[name] = stats
    text(36,467,'长治路正面 · 2021年1月街景机位',21,True)
    text(36,506,'左侧为门廊三拱，旧址铭牌嵌于中、右拱之间。',18)
    text(842,622,'山花下的大券窗',22,True)
    text(842,663,'2016年Fayhoo照片保留了上部',18)
    text(842,694,'窗框与外挑窗台。街景显示下方',18)
    text(842,725,'原有三个另设窗台的方窗，',18)
    text(842,756,'至2021年已封闭。',18)
    text(36,790,'2023年虹口区照片机位所见三拱与下排窗洞',20,True)
    text(36,838,'2021年刊发的另一幅现场近照可见通行门廊内的门扇、上亮窗和地坪。同期公开照片未给出改装的确切年月。',17)
    output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(output, quality=91, subsampling=0)
    return dict(file=output.name, sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                source_model_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(), source_photo_pixels=False, views=proof)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mesh',type=Path)
    p.add_argument('image',type=Path)
    p.add_argument('report',type=Path)
    a = p.parse_args()
    a.report.write_text(json.dumps(board(a.mesh,a.image),ensure_ascii=False,indent=2)+'\n')
