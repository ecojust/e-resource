"""Trace original photo marks into the actual GLB; distinguish baluster apertures by first-hit depth."""
from pathlib import Path
import argparse,hashlib,json,runpy,sys
import numpy as np
HERE=Path(__file__).absolute().parent
from register_court import Camera

# Each mark is specified in the documented photograph's working coordinates. No screen marks are generated from the model.
OBS={
 '03':{'front shaft':[(295,479),(488,485)],'rear shaft':[(225,408),(557,415)],
       'Ionic capital':[(297,325),(485,325)],'upper cornice':[(334,165),(481,166)],
       'bowed fascia':[(363,284),(408,285),(446,291)],'stair':[(393,684),(362,695)],
       'upper stem':[(316,137),(382,137),(408,137),(475,137)],
       'upper aperture':[(321,137),(388,138),(412,138),(481,137)],
       'bowed stem':[(345,247),(365,244),(402,243),(421,246)],
       'bowed aperture':[(355,245),(374,244),(392,245),(411,244)]},
 '04':{'rear shaft':[(771,507)],'upper stem':[(815,364),(843,359),(889,374)],'upper pier':[(862,367)],
       'upper aperture':[(822,360),(851,361),(883,367)],'upper cornice':[(832,432),(895,454)]},
 '05':{'front shaft':[(584,246),(690,236)],'rear shaft':[(372,225),(645,243)],
       'Ionic capital':[(593,54),(690,78)],'stair':[(530,414),(508,444),(503,470),(733,442)]}}
GREY='Fudefang | grey terrazzo';STEP='Fudefang | pale step stone'
def expected(category,hit):
    if hit is None:return 'aperture' in category
    x,y,z=hit['point_enu_m'];mat=hit['material']
    if category=='stair':return mat==STEP and -.05<=z<.7
    if category.startswith('upper ') and ('stem' in category or 'pier' in category or 'aperture' in category):
        rail=mat==GREY and .29<y<.68 and 7.71<z<8.70
        return not rail if 'aperture'in category else rail
    if category.startswith('bowed ') and ('stem' in category or 'pier' in category or 'aperture' in category):
        rail=mat==GREY and y<.16 and 4.15<z<5.02
        return not rail if 'aperture'in category else rail
    if mat!=GREY:return False
    if category=='front shaft':return abs(x)<1.25 and -.95<y<-.40 and .67<z<3.50
    if category=='rear shaft':return 1.89<abs(x)<2.48 and .36<y<.90 and .68<z<7.0
    if category=='Ionic capital':return abs(x)<1.26 and -.99<y<-.33 and 3.43<z<3.83
    if category=='bowed fascia':return y<.29 and 3.78<z<4.23
    if category=='upper cornice':return .24<y<1.80 and 7.13<z<7.80
    raise ValueError(category)
def scan(path):
    project=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
    api=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=api['SerialScene'](path);records=[]
    offsets=sorted((np.hypot(i,j),i,j)for i in range(-4,5)for j in range(-4,5)if np.hypot(i,j)<=4)
    for n,groups in OBS.items():
        cam=Camera(n,working=True)
        for kind,values in groups.items():
            for uv in values:
                nearest=None;raw=None
                for radius,dx,dy in offsets:
                    hit=scene.ray(cam.c,cam.ray(np.array(uv)+[dx,dy]),35)
                    if radius==0:raw=hit
                    if expected(kind,hit):
                        nearest=dict(radius_working_px=radius,offset=[dx,dy],hit=hit);break
                records.append(dict(photo=n,working_uv=uv,visible_target=kind,first_hit=raw,matched_exact=expected(kind,raw),matched=nearest))
    return {'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'count':len(records),'exact':sum(v['matched_exact']for v in records),'within_four_working_px':sum(v['matched']is not None for v in records),'observations':records}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=scan(a.mesh);a.out.write_text(json.dumps(r,indent=2)+'\n');print(r['count'],r['exact'],r['within_four_working_px'])
