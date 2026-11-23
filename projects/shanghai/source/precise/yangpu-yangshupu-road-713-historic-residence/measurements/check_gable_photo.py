"""Cast independent annotated upper-gable image samples into the selected actual GLBs."""
from pathlib import Path
import argparse,hashlib,json,sys,runpy
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from ornament_chart import P
from finishes import BRICK,STONE,RED,DARK_RED,METAL,BACK
from build_model import PROJECT
SAMPLES={
    'red facing': ([(740,600),(755,622),(810,595),(824,637),(859,626),(899,635),(940,630)],[BRICK]),
    'low brick neck': ([(779,551),(784,551),(788,549)],[BRICK]),
    'crest crown stone': ([(781,517),(786,517),(768,528),(796,529)],[STONE]),
    'crest red fan field and narrow ribs': ([(780,527),(785,524),(789,528),(774,536),(781,532),(790,531)],[DARK_RED,RED]),
    'grey shelf': ([(773,544),(792,540)],[STONE]),
    'grey ventilator keys and ring': ([(777,598),(766,620),(790,613),(777,632),(769,609),(784,627)],[STONE]),
    'ventilator blade intervals': ([(778,611),(778,614),(780,619),(776,622)],[METAL,BACK]),
    'left slope': ([(701,619),(713,609),(740,587)],[STONE]),
    'right slope': ([(833,570),(889,588),(947,609)],[STONE]),
    'sky above exposed crest': ([(778,505),(789,505),(823,530),(900,565)],[None])}
def check(path):
    scene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](path)
    origin=-np.linalg.solve(P[:,:3],P[:,3]);samples=[]
    def hit_at(p):
        ray=np.linalg.solve(P[:,:3],[*p,1.]);ray/=np.linalg.norm(ray)
        r=scene.ray(origin,ray,100);return r['material']if r else None
    for feature,(points,mats)in SAMPLES.items():
        for uv in points:
            actual=hit_at(uv)
            offsets=sorted([(x,y)for x in range(-2,3)for y in range(-2,3)if x*x+y*y<=4],key=lambda p:p[0]**2+p[1]**2)
            matches=[off for off in offsets if hit_at(np.asarray(uv)+off)in mats]
            samples.append(dict(feature=feature,observed_pixel=uv,expected=mats,central_ray=actual,central_match=actual in mats,nearest_matching_offset_px=matches[0] if matches else None))
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),central_hits=sum(q['central_match']for q in samples),within_two_pixels=sum(q['nearest_matching_offset_px'] is not None for q in samples),total=len(samples),samples=samples)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('roles',nargs='+',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[check(f) for f in a.roles];a.out.write_text(json.dumps(dict(photograph='Fayhoo, 2015-04-06',dimensions=[2053,1369],photo_sha256='050cf49f380c8e19fd67397519ee6ddff5d6767d392e8ab659e6a2594a2f3e45',tolerance_px=2,roles=rows),ensure_ascii=False,indent=2)+'\n')
    for q in rows:print(q['file'],q['central_hits'],q['within_two_pixels'],q['total'],[(x['feature'],x['observed_pixel'],x['central_ray'])for x in q['samples']if x['nearest_matching_offset_px']is None])
