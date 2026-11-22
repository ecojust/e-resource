"""Illustrate the side windows and rainwater detail at No.14 May Lee Court.

Run with an uncompressed full-detail GLB and the decoded low-detail GLB.
Use --wing-full for a side-wall component study before final assembly.
The garden camera and measured facade coordinates are the only photographic inputs.
Builds the adjacent MIT raster helper with cc. Requires NumPy, Pillow and Noto CJK.
"""
import argparse
import ctypes
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from photo_glb_raster import raster

HERE = Path(__file__).resolve().parent
PAPER = (251, 248, 241)
INK = '#292e28'
SECOND = '#586153'
LEAD = '#466456'
CLAY = '#a7563c'
RULE = '#beb8a8'
SIZE = (1460, 1020)


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def camera(eye, subject):
    eye = np.asarray(eye, dtype=float)
    axis = np.array(subject) - eye
    axis /= np.linalg.norm(axis)
    right = np.cross(axis, [0, 0, 1])
    right /= np.linalg.norm(right)
    down = np.cross(axis, right)
    axes = np.array([right * 1200, down * 1200, axis])
    return np.column_stack([axes, -axes @ eye])


def frame(rect, dimensions):
    x0, y0, x1, y1 = rect
    cx, cy = (x0+x1)/2, (y0+y1)/2
    w = max(x1-x0, (y1-y0) * dimensions[0]/dimensions[1])
    h = w * dimensions[1]/dimensions[0]
    return [cx-w/2, cy-h/2, cx+w/2, cy+h/2]


def box_projection(matrix, x, y, z):
    corners = np.array([(*v, 1) for v in itertools.product(x, y, z)])
    v = corners @ matrix.T
    xy = v[:, :2] / v[:, 2:3]
    return [*xy.min(axis=0), *xy.max(axis=0)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', required=True, type=Path)
    parser.add_argument('--lod', required=True, type=Path)
    parser.add_argument('--wing-full', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--font-dir', type=Path, default=Path('/usr/share/fonts/opentype/noto'))
    opt = parser.parse_args()
    opt.out.mkdir(exist_ok=True, parents=True)
    a = opt.wing_full or opt.full
    b = opt.full
    lod = opt.lod
    cam_file = HERE/'garden-corner-camera.json'
    glass_file = HERE/'garden-side-glass-tones.json'
    stone_file = HERE/'garden-quoin-drain.json'
    reference = np.asarray(read(cam_file)['main_corner_projection'])
    stones = read(stone_file)
    lights = read(glass_file)['levels']
    sample_counts = {k: sum(x['clear'] for x in v) for k, v in lights.items()}
    assert sample_counts == {'ground':12, 'middle':15, 'upper':16}
    assert sum(map(len, lights.values())) == 75 and len(stones['courses']) == 28
    assert sum(x['return_edge_px'] is not None for x in stones['courses']) == 26
    views = {}
    mid = camera((-15., 2.75, 6.02), (-3., 4.11, 5.20))
    side = camera((-33., 1.03, 6.3), (-3., 3.86, 5.04))
    sill = camera((-11.9, 1.42, 6.35), (-3., 4.17, 4.35))
    sun = np.array([-.80, -.25, .58], dtype=np.float32)
    sun /= np.linalg.norm(sun)

    @lru_cache(maxsize=32)
    def font(px, kind='regular'):
        family = 'NotoSerifCJK' if kind == 'title' else 'NotoSansCJK'
        weight = 'Bold' if kind in ('bold','title') else 'Regular'
        return ImageFont.truetype(str(opt.font_dir / f'{family}-{weight}.ttc'), px, index=2)

    def text(draw, xy, message, px=24, color=INK, style='regular'):
        draw.text(xy, message, font=font(px, style), fill=color, anchor='la')

    def sheet(title, sub):
        paper = Image.new('RGB', SIZE, PAPER)
        draw = ImageDraw.Draw(paper)
        text(draw, (54,25), '上海美丽园  ／  延安西路379弄14号', 23, LEAD, 'bold')
        text(draw, (51,60), title, 49, INK, 'title')
        text(draw, (54,132), sub, 22, SECOND)
        draw.line((54,177,1406,177), fill=RULE, width=2)
        return paper, draw

    def foot(draw, message):
        draw.line((54,939,1406,939), fill=RULE, width=2)
        text(draw, (54,956), message, 19, SECOND)

    def panel(paper, name, mesh, matrix, rect, xy, dims):
        crop = list(map(float, frame(rect, dims)))
        result, info = raster(mesh, lib, int(dims[0]*1.4), matrix, crop, sun, [253,35])
        assert info['zbuffer_foreground_pixels'] > 500 and info['textured_triangles'] > 0
        paper.paste(result.resize(dims, Image.Resampling.LANCZOS), xy)
        views[name] = dict(mesh_sha256=sha(mesh), camera=matrix.tolist(), **info)
        return info

    with tempfile.TemporaryDirectory(prefix='maylee-boards-') as temp:
        so = Path(temp)/'garden-render.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',HERE/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib = ctypes.CDLL(str(so))
        lib.paint.restype = lib.shadow_depth.restype = None
        image, draw = sheet('侧墙的三层钢窗', '三层深窗洞都有五列五行玻璃。窗台向庭院倾斜，棕色檐口沿墙角折转。')
        box = box_projection(side, (-3.64,-2.81), (1.13,6.03), (.17,10.25))
        panel(image, 'three genuine openings', a, side, box, (54,205), (439,696))
        text(draw,(54,906),'侧墙近正视  ·  近档',19,SECOND)
        text(draw,(530,204),'中层钢窗',28,INK,'bold')
        rect = box_projection(mid,(-3.14,-2.76),(3.28,5.04),(4.12,6.10))
        panel(image, 'middle casement', a, mid, rect, (530,253), (404,251))
        text(draw,(961,248),'三层玻璃的明暗',25,INK,'bold')
        for i,(k,label) in enumerate([('upper','上层'),('middle','中层'),('ground','下层')]):
            y = 312 + 54*i
            text(draw,(962,y),label,22,SECOND)
            for col in range(25):
                fill = LEAD if col < sample_counts[k] else '#dbd9ce'
                draw.rectangle((1033+9*col,y+7,1039+9*col,y+26),fill=fill)
            text(draw,(1271,y),f'{sample_counts[k]} / 25',21)
        text(draw,(962,478),'绿色为原图能读出颜色的格数。',19,SECOND)
        draw.line((530,535,1406,535),fill=RULE,width=2)
        text(draw,(530,554),'出挑窗台与下鼻',27,INK,'bold')
        rect = box_projection(sill,(-3.16,-2.81),(3.29,5.02),(4.01,4.55))
        panel(image, 'sloping sill', a, sill, rect, (530,611), (405,219))
        text(draw,(530,846),'台面由窗边向外降低，外端下方有滴水边。',19,SECOND)
        text(draw,(959,554),'檐口两面的浅色嵌板',27,INK,'bold')
        info = panel(image,'two fascia insets', a, reference, [104,51,320,214], (960,611), (445,219))
        assert info['materials_visible_samples'].get('Garden eave | pale inset face',0)>20
        text(draw,(960,846),'侧面与正面各一块，深色包边在角上连续。',19,SECOND)
        foot(draw,'原图可读出43格的颜色，其余32格按同层邻格估色。下层窗台受树叶遮挡，轮廓和坡度均作估计。')
        image.save(opt.out/'three-side-windows.png',optimize=True)

        image,draw = sheet('园侧隅石与雨水管', '从高参88的第93幅庭院照机位看，浅色隅石沿红砖转角逐道交错，暗色铁管紧贴正面。')
        total = panel(image, 'garden photograph 93 position', b, reference, [115,42,358,705], (54,205), (430,694))
        assert total['materials_visible_samples'].get('Garden corner | brown-black downpipe',0)>100
        text(draw,(54,906),'原片93机位投影  ·  近档',19,SECOND)
        text(draw,(520,205),'两面石缝的错接',27,INK,'bold')
        panel(image,'two-faced stone courses',b,reference,[219,226,283,334],(520,259),(404,274))
        text(draw,(520,547),'正面长石转过角，侧面随即缩短。',20,SECOND)
        text(draw,(960,205),'方形接水斗与弯颈',27,INK,'bold')
        head=panel(image,'square rainwater head',lod,reference,[276,88,323,163],(960,259),(445,274))
        assert head['materials_visible_samples'].get('Garden corner | weathered square rainwater head',0)>80
        text(draw,(960,547),'弯颈从檐边落入方斗，斗底接暗色圆管。',20,SECOND)
        draw.line((520,603,1405,603),fill=RULE,width=2)
        text(draw,(520,623),'相邻两道隅石的俯视尺寸',26,INK,'bold')
        for j,course in enumerate(stones['courses'][6:8]):
            x=540+435*j;y=820;scale=250
            front=course['front_length_m'];ret=course['return_length_m']
            d=round(scale*stones['stone_relief_m']);f=round(scale*front);r=round(scale*ret)
            draw.rectangle((x+d,y-r-7,x+f+8,y-d),fill='#e4ded0')
            draw.polygon([(x,y),(x+f,y),(x+f,y-d),(x+d,y-d),(x+d,y-r),(x,y-r)], fill='#c3ac84', outline='#68583f',width=2)
            text(draw,(x+147,710),f"自上第{course['course_from_top']}道",23,INK,'bold')
            text(draw,(x+147,754),f'正面约 {front:.2f} 米',21)
            text(draw,(x+147,797),f'侧面约 {ret:.2f} 米',21)
        text(draw,(520,879),'共28道可辨隅石。最下面两道的侧缘隐在花叶后，模型只绘可见正面。',19,SECOND)
        foot(draw,'照片发表于2014年8月12日。石高与伸出长度按照片估尺，铁管在花叶上缘处结束。')
        image.save(opt.out/'quoin-and-rainwater-head.png',optimize=True)
    imgs = {p.name:sha(p) for p in [opt.out/'three-side-windows.png',opt.out/'quoin-and-rainwater-head.png']}
    doc={'images':imgs,'inputs':{'wing':sha(a),'full':sha(b),'lod':sha(lod)},'measurements':{f.name:sha(f) for f in [cam_file,glass_file,stone_file]},'program':sha(Path(__file__)),'raster':{k:sha(HERE/k) for k in ['photo_glb_raster.py','photo_glb_raster.c']},'source_colour_counts':sample_counts,'views':views}
    (opt.out/'garden-detail-boards.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(imgs,flush=True)

if __name__=='__main__':
    main()
