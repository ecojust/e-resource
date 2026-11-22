"""Project the native Fayhoo photograph's marked roof pixels into a supplied actual GLB."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import sys

import numpy as np

MEAS=Path(__file__).resolve().parent
PFX='Shanyin dormer | '
# Several independent positions on each element are retained. Parts of the
# glass crossed by a branch or curtain were avoided when recording the points.
PROBES={
    'warm pale roughcast': [(641,250),(642,281),(744,249),(746,301),(993,223)],
    'warm white sash': [(654,272),(674,290),(698,274),(714,287),(731,299),(697,320)],
    'glazing': [(663,278),(684,288),(706,277),(723,309),(963,258),(963,290),(961,321)],
    'aged oxblood paint': [(689,164),(746,180),(931,195),(947,254),(977,314),(959,274),(960,305)],
    'pale verge flashing': [(707,157),(736,168),(765,181)],
    'weathered grey apron': [(647,334),(695,333),(743,334),(875,357),(922,357),(976,357)],
    'shadowed reveal':[(922,252),(922,287),(921,308)],
    'terracotta tile roll':[(875,165),(918,151),(952,141)],
}

SECOND_PROBES={
    'warm pale roughcast':[(214,60),(216,65),(247,66),(249,70)],
    'warm white sash':[(222,65),(234,61),(233,72),(244,62)],
    'glazing':[(226,64),(237,63),(313,71),(318,73)],
    'pale verge flashing':[(211,40),(226,35),(243,37)],
    'dark eaves gutter':[(282,37),(300,38),(315,40)],
    'shadowed reveal':[(301,59),(302,64),(301,70)],
    'aged oxblood paint':[(322,69),(323,74)],
}
SECOND_SHA='684e1640710675931ea01667869a0d8753225e9cc8eccf35d47bbd60b02fc86c'

def inspect(project,asset,layout,independent=False):
    sys.path.insert(0,str(project/'source/precise/xuhui-pathe-records-office/measurements/city-contact'))
    from glb_triangles import load_triangles
    tris,material,labels,_=load_triangles(asset)
    p=np.asarray(layout['camera_P'],float)
    inv=np.linalg.inv(p[:,:3]);center=-inv@p[:,3]
    a=tris[:,0];e1=tris[:,1]-a;e2=tris[:,2]-a;t0=center-a
    q=np.cross(t0,e1);num_t=np.einsum('ij,ij->i',e2,q)
    def closest(u,v):
        direction=inv@np.array([u,v,1.]);direction/=np.linalg.norm(direction)
        hp=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,hp);valid=np.abs(det)>1e-10
        dn=np.where(valid,det,1.);ru=np.einsum('ij,ij->i',t0,hp)/dn;rv=(q@direction)/dn;t=num_t/dn
        keep=valid&(ru>=0)&(rv>=0)&(ru+rv<=1)&(t>0)
        if not np.any(keep):return None
        idx=np.argmin(np.where(keep,t,np.inf))
        return {'material':labels[int(material[idx])], 'enu':np.round(center+t[idx]*direction,4).tolist()}
    rows=[]
    radius=2 if independent else 4
    for mat,probes in (SECOND_PROBES if independent else PROBES).items():
        for uv in probes:
            hit=closest(*uv);expected=PFX+mat
            matched=hit and hit['material']==expected
            nearest=None
            if not matched:
                candidates=sorted((dx*dx+dy*dy,dx,dy)for dx in range(-radius,radius+1)for dy in range(-radius,radius+1)if 0<dx*dx+dy*dy<=radius**2)
                for _,dx,dy in candidates:
                    alt=closest(uv[0]+dx,uv[1]+dy)
                    if alt and alt['material']==expected:nearest={'offset':[dx,dy],'first':alt};break
            rows.append(dict(uv=uv,expected_material=expected,first=hit,matched_center=bool(matched),within_tolerance=bool(matched or nearest),closest_match=nearest))
    result=dict(asset_sha256=sha256(asset.read_bytes()).hexdigest(),asset_bytes=asset.stat().st_size,photo_sha256=SECOND_SHA if independent else 'e01c70ff00fa37bff3202cf71a1f6e0ea6270a9ac2f2ebc205a78c632ce3eeb4',tested=len(rows),at_center=sum(row['matched_center']for row in rows),within_tolerance=sum(row['within_tolerance']for row in rows),radius_px=radius,rows=rows)
    if not independent:
        result['within_four_pixels']=result['within_tolerance']
        for row in rows:row['within_four_pixels']=row['within_tolerance']
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['project','glb','layout','output']:parser.add_argument(name,type=Path)
    parser.add_argument('--second-photo',action='store_true',help='Read the 640×432 second camera and its masked, separately observed probes.')
    args=parser.parse_args();layout=json.loads(args.layout.read_bytes())
    result=inspect(args.project.resolve(),args.glb,layout,args.second_photo)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['at_center'],result['within_tolerance'],result['tested'])
