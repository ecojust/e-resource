"""Check physical first intersections and original photographic pixels on both street wings."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PRECISE = HERE.parents[1]
sys.path[:0] = [str(HERE.parent/'source'),
                str(PRECISE/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from materials import STUCCO, PALE, BAND, FRAME, GLASS
from street_wings import WINGS, basis

EXPECTED = {'stucco': [STUCCO], 'pale': [PALE], 'rib': [BAND, PALE], 'glass': [GLASS], 'steel': [FRAME]}
RECORD = json.loads((HERE/'street-window-corbel-observations.json').read_bytes())


def placement(wing):
    a, _, along, outward = basis(wing)
    xaxis = along if wing == 'wulumuqi' else -along
    rotation = np.array([[*xaxis, 0], [*(-outward), 0], [0,0,1.]]).T
    origin = np.r_[a + along*WINGS[wing]['centre'], 0.]
    return rotation, origin


def project(matrix, point):
    p = matrix @ [*point, 1.]
    return p[:2]/p[2]


def check_mesh(path):
    scene = SerialScene(path)
    details = []
    def ray(group, name, eye, direction, expect, *, px=None, depth=None):
        hit = scene.ray(eye, direction, 95.)
        matched = bool(hit and hit['material'] in expect)
        if depth is not None:
            matched = bool(matched and abs(hit['point_enu_m'][2] - depth) <= .025)
        details.append(dict(group=group, feature=name, pixel=px, wanted=expect,
                            expected_z=depth, first=hit, matched=matched))
    for wing, data in WINGS.items():
        r, o = placement(wing)
        for idx in range(4):
            y = -.82 + (idx+.28)*.82/4
            z = 5.622-.148-idx*1.104/3
            for side in (-1,1):
                x = side * data['width']*.463
                ray(wing+' section',f'console {side:+} step {idx+1}',r@[x,y,3.20]+o,
                    r@[0,0,1.],[STUCCO,PALE],depth=z)
        for level,(lo,hi) in enumerate(((5.622,9.132),(9.132,12.718),(12.718,16.4)),3):
            for x in (-.73,0.,.73):
                for frac in (.38,.69):
                    ray(wing+' section',f'F{level} pane',r@[x,-1.8,lo+(hi-lo)*frac]+o,
                        r@[0,1.,0.],[GLASS])
            ray(wing+' section',f'F{level} central rib',r@[0,-1.8,lo+.25]+o,
                r@[0,1.,0.],[BAND,PALE])
    p = np.array(RECORD['P'])
    inv = np.linalg.inv(p[:,:3])
    local_eye = -inv@p[:,3]
    r, o = placement('fuxing')
    for feature,px,kind in RECORD['photo_samples_08']:
        ray('2023 housing close view', feature, r@local_eye+o, r@inv@[*px,1.],
            EXPECTED[kind], px=px)
    cam = json.loads((HERE/'corner-camera-and-levels.json').read_bytes())
    p = np.array(cam['cameras']['commons2015']['P'])
    inv = np.linalg.inv(p[:,:3]); eye = -inv @ p[:,3]
    for wing,picks in RECORD['photo_samples_commons2015'].items():
        for px in picks:
            ray('2015 '+wing, 'upper window',eye,inv@[*px,1.],[GLASS],px=px)
    groups = {}
    for row in details:
        tally = groups.setdefault(row['group'], {'matched':0, 'total':0})
        tally['matched'] += int(row['matched'])
        tally['total'] += 1
    return dict(mesh=scene.asset, groups=groups, rays=details)


def draw_registration(file):
    from PIL import Image, ImageDraw, ImageFont
    im=Image.new('RGB',(1080,650),'#f8f5ed');d=ImageDraw.Draw(im)
    def font(sz):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',sz)
    d.text((32,25),'Boissezon Apartments | Projecting street window',font=font(31),fill='#263c36')
    d.text((33,80),'2023 close view: marked corners and projected profiles',font=font(18),fill='#42514c')
    p=np.array(RECORD['P'])
    def px(uv):return (30+uv[0]*.66,118+uv[1]*.58)
    def project_point(v):return px(project(p,v))
    for x in (-1.525,1.525,-1.30,1.30):
        edge=[[x,-.822,5.622]]
        for i in range(4):
            z=5.474-i*1.104/3
            for step,offset in ((0.,0.),(.58,0.),(.58,-.025),(.78,-.025),(.78,-.049),(1.,-.049)):
                edge.append([x,-.822+(i+step)*.822/4,z+offset])
        d.line([project_point(v) for v in edge],fill='#445651',width=2)
    for z in (5.474,5.622):
        d.line([project_point([x,-.822,z]) for x in (-1.525,1.525)],fill='#445651',width=2)
    for row in RECORD['points']:
        x,y=px(row['pixel']);d.ellipse((x-3,y-3,x+3,y+3),outline='#b44d38',width=2)
    d.line((715,125,715,560),fill='#d0cbbd',width=2)
    f=RECORD['fitted']
    for i,line in enumerate(('Measured profile', 'Bay width       3.05 m',f"Projection      {f['projection_m']:.3f} m",
                           f"Console width  {f['console_width_m']:.3f} m",f"4-step drop     {f['drop_from_first_to_fourth_nose_m']:.3f} m",
                           f"Median error    {f['median_px']:.2f} px",'15 traced corners')):
        d.text((744,150+43*i),line,font=font(18 if i else 22),fill='#334943')
    d.text((32,590),'Red circles reproduce measured pixels. Lines project the model. No source pixels are embedded.',
           font=font(17),fill='#52625b')
    im.save(file,quality=92)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    cli.add_argument('--plate',type=Path);args=cli.parse_args()
    report=check_mesh(args.mesh)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if args.plate: draw_registration(args.plate)
    print(json.dumps(report['groups']))
