"""Intersect 34 photo observations from three dated stations with the first exported triangle."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from register_street import Camera
HERE=Path(__file__).resolve().parent
LIB=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
Scene=runpy.run_path(str(LIB/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
M={
    'upper roughcast':'coarse cream finish above brick','individual glazed lights':'smoke green side window glass',
    'single sloping green sheet':'green sheet on upper lane awning','red unit facing':'red facing units with pale mortar',
    'light rendered opening panel':'pale buff lane window panel','outward glazing':'smoke green side window glass',
    'exposed shaded opening':'shadow behind open lane casement','outward leaf':'weathered lane steelwork',
    'plinth':'blue grey rendered plinth','dark gate grille':'weathered lane steelwork','lower doorway deep shadow':'shadow behind open lane casement',
    'air inlet':'dark condenser intake','horizontal grille':'old ivory condenser housing','condenser box':'old ivory condenser housing'}
def verify(asset):
    scene=Scene(asset)
    rows=json.loads((HERE/'lane-return-ray-pixels.json').read_bytes())
    out={}
    for station,rec in rows.items():
        c=Camera(station); samples=[]; native_per_pixel=c.size[0]/1050
        for q in rec['samples']:
            p=np.array(q['pixel'])
            materials=['Xinlefang | '+M[n] for n in q['expected_part']]
            actual=scene.ray(c.c,c.ray(p),55)
            hit=actual and actual['material'] in materials
            closest=None
            for radius in [0, .5,1,2,3,5,8]:
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(.707,.707),(.707,-.707),(-.707,.707),(-.707,-.707)):
                    offset=native_per_pixel*radius*np.array([dx,dy]);h=scene.ray(c.c,c.ray(p+offset),55)
                    if h and h['material'] in materials:
                        closest=radius;break
                if closest is not None:break
            samples.append({'source_pixel':q['pixel'],'feature':q['feature'],'expected_materials':materials,'first_hit':actual,'matches':bool(hit),'nearest_match_search_1050_width_px':closest})
        out[station]={'source_sha256':rec['photograph_sha256'],'count':len(samples),'exact':sum(r['matches']for r in samples),
          'within_3_at_1050_width':sum(r['nearest_match_search_1050_width_px'] is not None and r['nearest_match_search_1050_width_px']<=3 for r in samples),'samples':samples}
    return {'mesh_sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'triangles':len(scene.tri),'stations':out}
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('glb',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
    r=verify(args.glb);args.output.write_text(json.dumps(r,indent=2)+'\n');print({k:(v['exact'],v['within_3_at_1050_width'],v['count'])for k,v in r['stations'].items()})
