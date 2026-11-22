"""Trace the first physical intersection from the original No.9/11 photograph pixels."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles

GROUPS={
    'paint':['white painted brick','pale moulding','shallow painted joints'],
    'brick':['fired red brick','dull red recessed face','rubbed terracotta','recessed carving'],
    'green':['enamel green plate','painted sign white'],
    'fan9':['No.9 dimpled glazing'],
    'fan11':['No.11 surviving light pane','No.11 dark horizontal slats'],
    'wood':['dark timber'],
    'stone':['worn grey step'],
    'recess-wall':[], 'recess-floor':[], 'no9-depth':['gate iron'],
}

def inspect(asset,settings):
    tris,ids,names,_=load_triangles(asset);result=[]
    a=tris[:,0];e=tris[:,1]-a;f=tris[:,2]-a
    def one(P,uv):
        inv=np.linalg.inv(P[:,:3]);origin=-inv@P[:,3];ray=inv@[*uv,1];ray/=np.linalg.norm(ray)
        q=origin-a;h=np.cross(ray,f);det=np.einsum('ij,ij->i',e,h)
        active=np.abs(det)>1e-10;safe=np.where(active,det,1)
        u=np.einsum('ij,ij->i',q,h)/safe;s=np.cross(q,e);v=(s@ray)/safe
        distance=np.einsum('ij,ij->i',s,f)/safe
        success=active&(u>=0)&(v>=0)&(u+v<=1)&(distance>0)
        if not success.any():return None
        closest=int(np.argmin(np.where(success,distance,np.inf)))
        return dict(material=names[int(ids[closest])],xyz=(origin+ray*distance[closest]).round(5).tolist())
    for key,photo in settings['photos'].items():
        P=np.array(settings['cameras'][key])
        for expected,points in photo['original_probes'].items():
            for uv in points:
                hit=one(P,uv);labels=['Courtyard door | '+n for n in GROUPS[expected]]
                if expected=='paint':labels.append('Wujin courtyard | whitewashed brick')
                if expected=='recess-wall':labels+=['Wujin courtyard | warm plaster in recess']
                if expected=='recess-floor':labels+=['Wujin courtyard | grey interior floor']
                if expected=='no9-depth':labels+=['Wujin courtyard | unlit enclosed doorway']
                match=bool(hit and hit['material'] in labels)
                if match and expected in ('recess-wall','recess-floor','no9-depth'):
                    match=hit['xyz'][1]>.20
                result.append(dict(photograph=key,uv=uv,expected=expected,first=hit,match=match))
    counts={k:{'centres':sum(i['match']for i in result if i['photograph']==k),'rays':sum(i['photograph']==k for i in result)}for k in settings['photos']}
    return dict(asset_sha256=sha256(asset.read_bytes()).hexdigest(),triangles=len(tris),counts=counts,points=result)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('asset',type=Path);parser.add_argument('result',type=Path)
    opt=parser.parse_args();data=json.loads((HERE/'paired-door-photographs.json').read_bytes());report=inspect(opt.asset,data)
    opt.result.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print(report['counts'])
