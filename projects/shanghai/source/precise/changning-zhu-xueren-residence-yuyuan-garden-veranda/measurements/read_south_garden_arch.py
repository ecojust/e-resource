"""Read the crown and jambs of the projecting central garden bay in Gao Can's 2013 original."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ORIGINAL_SHA256 = 'e76712e95e77aaf485668b4312c2fe5fe422678f30eb8247b6659bc8f9e157c8'
SAMPLES = [244,252,262,272,284,298,312,326,342,357,372,387,402,417,432,447,462,477,492,507,522,537,549,558]
# Read the wall edges at the bottom of the cornice and at the front of the upper landing. The rear door threshold lies behind this plane.
# Their small tilt is visible in the masonry courses on each side.
CENTRAL_REFERENCE = [[168.5,121.5],[629.5,122],[635.0,392.5],[157.5,393.5]]


def projected_grid(uv):
    basis = np.asarray(CENTRAL_REFERENCE, dtype=float)
    target = [(0,1),(1,1),(1,0),(0,0)]
    rows, values = [], []
    for (u,v),(x,z) in zip(basis,target):
        rows += [[u,v,1,0,0,0,-x*u,-x*v], [0,0,0,u,v,1,-z*u,-z*v]]
        values += [x,z]
    project = np.append(np.linalg.solve(rows,values),1).reshape(3,3)
    t = project @ [*uv,1]
    return np.round(t[:2]/t[2],6).tolist()


def read(photo):
    assert hashlib.sha256(photo.read_bytes()).hexdigest() == ORIGINAL_SHA256
    image = np.asarray(Image.open(photo).convert('RGB'),dtype=float)
    assert image.shape == (533,800,3)
    samples = []
    for x in SAMPLES:
        guess = round(148 + .00148*(x-402)**2)
        col = image[:,x-1:x+2].mean(axis=1)
        options = []
        for y in range(guess-6,guess+7):
            above,below = col[y-2:y].mean(axis=0),col[y:y+2].mean(axis=0)
            drop = above.mean()-below.mean()
            warmer = (above[2]-above[0])-(below[2]-below[0])
            options.append((drop+.75*warmer,y))
        score, y = max(options)
        samples.append(dict(uv=[x,y], relative_x_z=projected_grid((x,y)), local_edge_score=round(score,2)))
    return dict(source='https://s13.sinaimg.cn/orignal/001HIrzOgy6IyKC4Keg2c',sha256=ORIGINAL_SHA256,
                size=[800,533],original_capture='2013-09-26 14:45:08',camera='Nikon D3000 / 27 mm equivalent',
                plane='南园廊中部略前出的立面。x取该段两侧外边的相对宽，z由台阶平台至二层挑檐下口按0到1归一化。两轴尺度分别定义。',
                reference_pixels=CENTRAL_REFERENCE,arc_trace=samples,
                jamb_pixel_pairs={'west':[[240,188],[235,320]],'east':[[561,188],[565,320]]},
                upper_finish='弧口上有窄灰色收边，边缘随弧线；深色阴影位于洞内。总计24个像素列沿灰边与暗色券底交界读数。',
                central_floor='两樘后墙深色双扇玻璃门，门槛在同一层位。中央有花园台阶，两侧低栏与花池。',
                rear_door_stiles_and_transoms={'west':[[321,219],[396,219],[396,366],[321,366]],'east':[[467,221],[542,221],[542,361],[467,361]],'west_transom_y':248,'east_transom_y':250},
                limits='相对坐标用于模型形状整合；廊深、绝对标高、相机畸变，以及后墙和正面之间的视差需分面处理。')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.write_text(json.dumps(read(args.photo),ensure_ascii=False,indent=2)+'\n')
