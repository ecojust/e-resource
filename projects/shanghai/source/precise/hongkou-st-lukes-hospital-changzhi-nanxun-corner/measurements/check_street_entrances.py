"""Read every triangle in a model and check the frontmost hit at observed photo positions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles

# Labels describe surfaces visible in the source. People, street poles and greenery were excluded.
POINTS={
 'district_2023':{
  'plaque':[(213,1018),(217,1020),(219,1023)],
  'exhibition':[(43,1024),(46,1046),(109,1034),(114,1044),(191,1029),(194,1041),(305,1041),(306,1056)],
  'stucco':[(523,981),(530,985),(546,978),(573,977),(605,985),(613,986),(956,977),(959,981),(1067,979)],
  'lower':[(278,1045),(355,1050),(359,1065)],
  'upper':[(368,924),(368,930),(358,918)]},
 'street_2021':{
  'upper':[(948,323),(982,332),(1000,344),(1024,362),(861,360),(905,373),(981,374)],
  'upper_glass':[(935,353),(947,349),(956,372),(991,371),(891,371)],
  'lower':[(878,460),(884,475),(945,466),(951,479),(1009,471)],
  'exhibition':[(572,431),(578,443),(669,438),(685,445),(772,443)],
  'plaque':[(721,443)]},
 'fayhoo_2016_gable':{
  'upper':[(1598,981),(1598,990),(1563,987),(1531,1028),(1626,986),(1653,1018),(1524,1035),(1662,1035),
           (1569,1051),(1625,1059),(1567,1068),(1626,1072)],
  'upper_glass':[(1581,1040),(1590,1049),(1601,1053),(1604,1067)],
  'lower':[(1598,1176),(1609,1180),(1654,1170)]}}


def cameras():
    j=json.loads((HERE/'changzhi-street-entrance-cameras.json').read_bytes())
    R=np.array(j['district_R']);K=np.array(j['district_K']);E=np.array(j['district_layout']['city_eye'])
    D=np.diag([1080/835,1164/900,1])
    return {'district_2023':D@K@np.c_[R,-R@E],'street_2021':np.array(j['street_P']),'fayhoo_2016_gable':np.array(j['fayhoo_gable_P'])}


def accepts(kind,m):
    if not (m or '').startswith('Street entrances |'):return False
    material=m.split('| ')[1]
    if kind=='plaque':return material in ('black bronze plaque','gilt plaque detail')
    if kind=='exhibition':return material in ('exhibition infill','inset panel')
    if kind=='lower':return material in ('exhibition infill','inset panel','shaded plaster reveals','grey sill and terrazzo')
    if kind=='stucco':return material in ('ivory rendered plaster','pale moulded dressings')
    if kind=='upper_glass':return material in ('aged dark casement glass','dark casement and timber')
    return material in ('shaded plaster reveals','pale moulded dressings','dark casement and timber','grey sill and terrazzo')


def check(mesh):
    triangles,indices,materials,info=load_triangles(mesh)
    results={}
    for image,P in cameras().items():
        a=triangles[:,0];edge1=triangles[:,1]-a;edge2=triangles[:,2]-a
        inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3];oc=eye-a
        nn=np.cross(oc,edge1);ds=np.einsum('ij,ij->i',nn,edge2)
        proj=triangles.reshape(-1,3)@P[:,:3].T+P[:,3];z=proj[:,2].reshape(-1,3)
        xy=(proj[:,:2]/np.where(abs(proj[:,2:3])>1e-12,proj[:,2:3],1)).reshape(-1,3,2)
        lo=xy.min(axis=1);hi=xy.max(axis=1);near=z.min(axis=1)<=0;visible=z.max(axis=1)>0
        def hit(px):
            ids=np.flatnonzero(visible&(((lo<=px).all(axis=1)&(hi>=px).all(axis=1))|near))
            if not len(ids):return None
            v=inv@[*px,1.];v/=np.linalg.norm(v);h=np.cross(v,edge2[ids]);det=np.einsum('ij,ij->i',edge1[ids],h)
            ok=abs(det)>1e-10;s=np.where(ok,det,1)
            u=np.einsum('ij,ij->i',oc[ids],h)/s;b=(nn[ids]@v)/s;t=ds[ids]/s
            good=np.flatnonzero(ok&(u>=0)&(b>=0)&(u+b<=1)&(t>1e-5))
            return materials[indices[ids[good[np.argmin(t[good])]]]] if len(good) else None
        rows=[]
        for kind,spots in POINTS[image].items():
            for px in spots:
                m=hit(px);radius=0 if accepts(kind,m) else None
                if radius is None:
                    for r in (1,2,3):
                        if any(accepts(kind,hit(px+r*np.array([np.cos(t),np.sin(t)])))for t in np.arange(8)*np.pi/4):radius=r;break
                rows.append(dict(feature=kind,uv=px,first=m,nearest_pixels=radius))
        results[image]=dict(total=len(rows),direct=sum(x['nearest_pixels']==0 for x in rows),within_three=sum(x['nearest_pixels'] is not None for x in rows),observations=rows)
    return dict(meshSHA256=hashlib.sha256(mesh.read_bytes()).hexdigest(),whole_model_triangles=len(triangles),views=results)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();result=check(args.mesh);args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print([(key,r['direct'],r['within_three'],r['total'])for key,r in result['views'].items()])
