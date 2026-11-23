"""Read finished GLB triangles along fixed locations on two independent photographs."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
D=Path(__file__).resolve().parent
PROJECT=next(p for p in D.parents if (p/'tools/package_architectural_model.py').is_file())
Scene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
samples={
'fayhoo':{'roughcast':[(143,482),(258,655),(192,451),(403,402),(525,438),(623,390),(779,421),(804,676),(778,199),(835,207),(609,136),(821,69)],'glazing':[(202,537),(239,565),(275,577),(393,585),(552,562),(539,324),(429,306),(506,345),(727,592),(846,536),(718,327),(788,309),(669,303),(656,598)],'tile':[(230,303),(291,300),(375,235),(485,228),(549,231),(645,91)],'coping':[(800,642),(775,368),(198,630)],'air':[(55,340),(930,275),(293,174),(569,65)]},
'restoration':{'roughcast':[(332,418),(403,470),(390,370),(442,332),(567,348),(680,357),(710,470),(710,209),(635,225),(746,96)],'glazing':[(367,410),(390,426),(475,430),(543,407),(485,282),(569,291),(673,417),(724,415),(673,260),(724,280)],'tile':[(381,279),(417,279),(473,229),(533,223),(562,225)],'coping':[(694,458),(688,309)],'air':[(300,350),(792,313),(530,155),(680,88)]}}
def hits(path):
    sc=Scene(path);spec=json.loads((D/'garden-front-registration.json').read_bytes());out={}
    classes={'roughcast':['yellow roughcast'],'glazing':['reflected grey blue glazing','shaded olive glazing','dark green steel'],'tile':['green glazed pan tiles'],'coping':['grey beige coping'],'air':['air']}
    offsets=sorted([(x,y)for x in range(-2,3)for y in range(-2,3)if x*x+y*y<=4],key=lambda q:q[0]*q[0]+q[1]*q[1])
    for name,groups in samples.items():
        cam=spec['photos'][name];P=np.array(cam['matrix']);eye=np.array(cam['eye']);A=np.linalg.inv(P[:,:3]);rows=[]
        def cast(uv):
            d=A@np.r_[uv,1.];d/=np.linalg.norm(d);hit=sc.ray(eye,d,60)
            return 'air' if hit is None else hit['material'].split(' | ',1)[-1]
        for k,pixels in groups.items():
            for px in pixels:
                first=cast(px);best=None
                for off in offsets:
                    if cast(np.array(px)+off) in classes[k]:best=off;break
                rows.append(dict(pixel=px,category=k,observed_first_surface=first,matches_centre=first in classes[k],nearest_photo_offset_pixels=best))
        out[name]=dict(centre=sum(r['matches_centre']for r in rows),within_two_pixels=sum(r['nearest_photo_offset_pixels']is not None for r in rows),total=len(rows),samples=rows)
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),results=out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',nargs='+',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    rows=[hits(path)for path in a.mesh]
    a.out.write_text(json.dumps(dict(method='Rays from two released photographic projections, through 70 preselected pixels. Window panes and their steel framing are a single class. A tolerance of two working-image pixels is reported separately.',roles=rows),ensure_ascii=False,indent=2)+'\n')
    for i in rows:print(i['file'],[(k,r['centre'],r['within_two_pixels'],r['total'])for k,r in i['results'].items()])
