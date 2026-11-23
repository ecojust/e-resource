"""Rectify the outer west pillar and four neighbouring window apertures from Masa frame 43034625."""
import argparse
import hashlib
import json
from pathlib import Path
from register_court import Camera

# Outer corners in the original 650 × 487 file. The tree obscures the two lower
# left jambs; their approximate pixels encode a wall opening, not hidden joinery.
OPENINGS = {
    'west-end.top4': [(113,132),(151,123),(148,158),(109,166)],
    'west-end.middle3': [(105,203),(143,195),(138,234),(101,240)],
    'west-end.lower2': [(91,274),(133,270),(127,318),(84,322)],
    'west-end.ground': [(62,367),(116,364),(110,417),(60,415)],
}
VISIBILITY = {
    'west-end.top4': 'Head, sill and east jamb visible. Tree partly covers west edge.',
    'west-end.middle3': 'Right portion and sill visible behind laundry and tree. West jamb estimated.',
    'west-end.lower2': 'Opening partly visible through leaves. Head and width uncertain.',
    'west-end.ground': 'Metalwork and vegetation obscure window subdivisions and most of the west jamb.',
}
def survey(camera):
    windows = []
    for name, corners in OPENINGS.items():
        xyz = [camera.wall(uv) for uv in corners]
        tl,tr,br,bl = xyz
        bounds = [(tl[0]+bl[0])*.5,(bl[2]+br[2])*.5,(tr[0]+br[0])*.5,(tl[2]+tr[2])*.5]
        windows.append({'opening': name, 'pixels_tl_tr_br_bl': corners,
                        'bounds_x0_z0_x1_z1':[round(float(n),4) for n in bounds],
                        'visibility': VISIBILITY[name]})
    ends = [(86,123),(51,345)]
    return {'image':'masa-43034625-650','sha256':'4ad01b07ae017279cc1901ce37b6c7c8056611e6ea99c4607aa80d0d882bfb98',
            'windows':windows,'west_masonry_edge_pixels':ends,
            'west_masonry_edge_x_readings_m':[round(float(camera.wall(uv)[0]),4) for uv in ends],
            'adopted_west_edge_x_m':-10.98,
            'limits':'Single oblique view. The two facade edge readings span 0.40 m. The two obscured lower openings are approximate; no hidden plan or precise return width is known.'}

if __name__ == '__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,default=Path(__file__).with_name('west-wing-openings.json'))
    cli.add_argument('--photo',type=Path,help='Optional privately obtained original to verify provenance')
    args=cli.parse_args()
    result=survey(Camera('25'))
    if args.photo:
        with args.photo.open('rb') as src:
            assert hashlib.file_digest(src,'sha256').hexdigest()==result['sha256']
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
