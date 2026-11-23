"""Inverse projection of observed garden-side roof edges onto candidate depth planes."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OBSERVATIONS = [
    ("garden tile drip west", 309, 204, 0.64),
    ("garden tile drip centre", 521, 205, 0.64),
    ("garden tile drip east", 626, 204, 0.64),
    ("cross wing ridge W", 493, 114, -6.08),
    ("cross wing ridge E", 644, 113, -6.08),
    ("small dormer front lip W", 397, 129, -1.38),
    ("small dormer front lip E", 480, 129, -1.38),
    ("small dormer sash LL", 416, 181, -1.63),
    ("small dormer sash UR", 469, 146, -1.63),
    ("hipped dormer front lip W", 509, 137, -1.21),
    ("hipped dormer front lip E", 645, 136, -1.21),
    ("hipped dormer sash LL", 524, 188, -1.56),
    ("hipped dormer sash UR", 623, 150, -1.56),
    ("hipped dormer crown", 575, 102, -2.63),
    ("west slim chimney cap", 372, 134, -4.84),
    ("wide central chimney cap", 547, 87, -6.3),
    ("short balcony W end", 346, 311, 0.33),
    ("short balcony slider W head", 368, 244, 0),
    ("short balcony slider E head", 423, 242, 0),
]


def point_at_depth(camera, u, v, out):
    """Return house X, Y, Z at the given outward offset from the garden wall."""
    u0,v0,scale,k,dv,ds,yaw,roll=camera
    u-=u0
    v-=v0
    a,b,c,d=scale-u*yaw,roll,-roll-v*yaw,-scale
    e=u*(1-k*out)-ds*out
    f=v*(1-k*out)-dv*out
    det=a*d-b*c
    east=(e*d-b*f)/det
    z=2.96+(a*f-e*c)/det
    return [round(n,4) for n in (9.55-east,13.60+out,z)]


def main():
    data=json.loads((HERE/'south-garden-two-photographs.json').read_text())
    camera=data['views']['0']['camera_coefficients']
    trials=json.loads((HERE/'garden-roof-camera-sensitivity.json').read_text())['coefficients_by_focal_pixels']
    rows=[]
    for label,u,v,d in OBSERVATIONS:
        rows.append(dict(feature=label,observed_native_px=[u,v],assumed_outward_m=d,
                         at_assumed_depth=point_at_depth(camera,u,v,d),
                         focal_trials_at_assumed_depth={k:point_at_depth(c,u,v,d) for k,c in trials.items()},
                         depth_sensitivity_m=[point_at_depth(camera,u,v,d-.65),point_at_depth(camera,u,v,d+.65)]))
    doc=dict(source=data['source_url'],photo_sha256=data['views']['0']['photo_sha256'],
             observation='Native 1080 by 720 pixel positions in the garden-gate photograph.',
             model_datum='X increases west, Y increases south, Z upwards. The central upper balcony floor is assumed at 2.96 m.',
             depth_limit='Roof edges lie at different distances behind or in front of the garden wall. The alternative columns recalculate their positions after varying each assumed depth by 0.65 m.',
             camera_coefficients=camera,features=rows)
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);target=p.parse_args().output
    string=json.dumps(doc,ensure_ascii=False,indent=2)+'\n'
    if target:target.write_text(string)
    else:print(string,end='')


if __name__=='__main__':main()
