"""Check the actual exterior, indoor painted glass and the rooftop cover in each exported mesh."""
from pathlib import Path
import argparse,hashlib,json,runpy,struct
import numpy as np
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/huangpu-central-trust-beijing-front/source'
READER=HERE.parent/'postal-office-v1/independent-glb-review-helpers.py'
load=runpy.run_path(READER)['load_triangles']
first=runpy.run_path(HERE.parent/'somekh-building-street-corner-v1/verify-export.py')['first']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def probes():
    plan=json.loads((SOURCE/'plan-registration.json').read_text())
    center=plan['south_width_m']/2
    a,b,c,d=np.array(plan['hall_opening_xy_m'])
    width=(np.linalg.norm(b-a)+np.linalg.norm(c-d))/2
    length=(np.linalg.norm(d-a)+np.linalg.norm(c-b))/2
    rows=[]
    def add(name,orig,ray,mats,near,far):rows.append((name,np.asarray(orig),np.array(ray,dtype=float),mats,near,far))
    def frontal(name,x,z,mat,lo,hi):
        add(name,(center+x,-4.,z),(0,1,0),[mat],4.+lo,4.+hi)
    axes=(-8.55,-6.70,-4.72,-1.90,0,1.90,4.72,6.70,8.55)
    for i,x in enumerate(axes):
        for z in (8.3,12.5,16.8,20.9):
            frontal(f'Original office aperture {i+1}',x+.18,z,'Trust smoky office glass',.300,.330)
        for z in (25.38,28.20):frontal(f'Added storey aperture {i+1}',x+.155,z,'Trust smoky office glass',.80,.84)
        if i not in (3,4,5):
            frontal(f'Steel lower opening {i+1}',x+.15,2.69,'Trust smoky office glass',.30,.33)
        if i%3==1:
            for z in (10.7,15.05,19.20):
                frontal('Spandrel floral relief',x+.11,z+.002,'Trust incised artificial stone',-.110,-.095)
    for x in (-1.55,1.55):
        frontal('Fluted stone shaft',x,2.6,'Trust entry pale stone',-.09,-.06)
        frontal('Freestanding square base',x,.09,'Trust entry pale stone',-.20,-.18)
        for side in (-1,1):
            frontal('Scroll cushion',x+side*.224,4.936,'Trust entry cut relief',-.105,-.085)
    for x in (-2.26,2.26):frontal('Recessed rear wall',x,2.,'Trust entry stone in shadow',1.29,1.32)
    for x,z in ((.463,1.47),(-.398,2.1)):frontal('Inner glazed doors',x,z,'Trust entry warm glazing',1.23,1.27)
    def well(name,u,v,up,mats):
        xy=(1-u)*(1-v)*a+u*(1-v)*b+u*v*c+(1-u)*v*d
        add(name,(*xy,5. if up else 34.),(0,0,1 if up else -1),mats,5.50 if up else 22.4,5.85 if up else 23.6)
    pad=width*.185;bay=(length-2*pad)/6
    for i in range(1,5):
        v=(pad+(i+.5)*bay)/length
        for feature,u,mat in [('opal roundel',.53,'Trust skylight antique ivory'),('roundel lead',.50,'Trust skylight antique lead'),('brass ring',.598,'Trust skylight reeded brass')]:
            well(feature,u,v,True,[mat])
    well('Green scale margin',.12,.36,True,['Trust skylight emerald','Trust skylight leaf green'])
    for u,v in ((.15,.18),(.35,.31),(.68,.67),(.82,.82)):
        well('Upper weather surface',u,v,False,['Trust skylight grey weather glass'])
    well('Metal ridge',.50,.51,False,['Trust skylight zinc bars'])
    for idx,corner in enumerate((a,b,c,d)):
        next_corner=(a,b,c,d)[(idx+1)%4];vector=next_corner-corner
        tangent=vector/np.linalg.norm(vector);out=np.array([tangent[1],-tangent[0]])
        for z in (12.5,16.7,21.2):
            position=.5 if idx in (0,2) else .125-.72/np.linalg.norm(vector)
            pos=corner+position*vector+tangent*.15
            add('Court steel window '+str(idx+1),(*(pos-out*.7),z),(*out,0),['Trust smoky office glass'],.92,1.02)
    return rows

def verify(path):
    tri,indices,names,info=load(path)
    attrs=(tri,tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],tri.min(axis=1),tri.max(axis=1))
    rows=[]
    for name,eye,ray,materials,near,far in probes():
        hit=first(*attrs,eye,ray);material=names[indices[hit[0]]]if hit else None
        distance=hit[1] if hit else None
        rows.append(dict(feature=name,origin=eye.tolist(),direction=ray.tolist(),expected_material=materials,
            expected_depth_m=[near,far],observed_material=material,depth_m=distance,
            passed=bool(hit and material in materials and near<distance<far)))
    with path.open('rb')as reader:
        reader.seek(12);size,_=struct.unpack('<II',reader.read(8));doc=json.loads(reader.read(size))
    glass=next(m for m in doc['materials']if m['name']=='Trust skylight grey weather glass')
    assert glass['alphaMode']=='BLEND'and abs(glass['pbrMetallicRoughness']['baseColorFactor'][3]-.27)<1e-5
    return dict(path=path.name,sha256=sha(path),triangles=len(tri),materials=len(names),cover_alpha=.27,checks=rows,passed=all(r['passed']for r in rows))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('models',nargs=3,type=Path);a=p.parse_args()
    variants=[verify(f)for f in a.models]
    a.out.write_text(json.dumps(dict(reader_sha256=sha(READER),variants=variants,passed=all(v['passed']for v in variants)),indent=2)+'\n')
    for v in variants:
        bad=[(x['feature'],x['origin'],x['observed_material'],x['depth_m'])for x in v['checks']if not x['passed']]
        print(v['path'],len(v['checks']),len(bad),bad[:18])
    raise SystemExit(not all(v['passed']for v in variants))
