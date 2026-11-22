"""Check the visible photo points and recessed facing-unit joints in decoded published meshes."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np


HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"source"))
from fuzhou_photo_plane import CAMERAS
from fuzhou_masonry import BED, PALE, DIRECT
from shopfront import DATA, rect
from upper_bookshop_windows import openings

def first_surfaces(tri,mi,names,cam,first_hit):
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);eye=-np.linalg.solve(cam[:,:3],cam[:,3])
    vertices=tri.reshape(-1,3)@cam[:,:3].T+cam[:,3]
    proj=(vertices[:,:2]/vertices[:,2,None]).reshape(-1,3,2);mn=proj.min(1);mx=proj.max(1);inverse=np.linalg.inv(cam[:,:3]);tiles={}
    def closest(xy):
        uv=np.asarray(xy);key=tuple(np.floor(uv/28.).astype(int))
        if key not in tiles:
            corner=np.array(key)*28.
            tiles[key]=np.flatnonzero((mn<=corner+28.).all(1)&(mx>=corner).all(1))
        ii=tiles[key];ray=inverse@np.r_[uv,1.];ray/=np.linalg.norm(ray)
        ii=ii[(mn[ii]<=uv+.0001).all(1)&(mx[ii]>=uv-.0001).all(1)&(n[ii]@ray<0)]
        if not len(ii):return None
        hit,dist,_=first_hit(tri[ii],eye,ray)
        return names[mi[ii[hit]]] if np.isfinite(dist) else None
    return closest

def check(mesh,project):
    tools=runpy.run_path(project/"data/audit/postal-office-v1/independent-glb-review-helpers.py")
    tri,mi,names,asset=tools["load_triangles"](mesh)
    photo=first_surfaces(tri,mi,names,CAMERAS["2015_street"],tools["first_hit"])
    reading=json.loads((HERE/"fuzhou-facing-witnesses.json").read_bytes())
    photo_points=[]
    for rec in reading['points']:
        face=photo(rec['native_px'])
        photo_points.append({'opening':rec['opening'],'pixel':rec['native_px'],'first_face':face,'visible_pale':face in [BED,*PALE]})
    # Inspect the four lower photographed panels normal to their physical faces.
    # This isolates the applied masonry from street furniture and the projecting
    # retail fascia obscuring the lowest strip in the photographer's view.
    near=tri[:,:,1].min(1)<.04
    near&=tri[:,:,1].max(1)>-.06
    near&=(tri[:,:,0].max(1)>-12.7)&(tri[:,:,0].min(1)<-7.)
    near&=(tri[:,:,2].max(1)>8.)&(tri[:,:,2].min(1)<10.)
    ii=np.flatnonzero(near)
    t=tri[ii];xmin,xmax=t[:,:,0].min(1),t[:,:,0].max(1);zmin,zmax=t[:,:,2].min(1),t[:,:,2].max(1)
    def normal_hit(x,z):
        sel=np.flatnonzero((xmin<=x+1.e-7)&(xmax>=x-1.e-7)&(zmin<=z+1.e-7)&(zmax>=z-1.e-7))
        if not len(sel):return None,None
        k,dist,pt=tools["first_hit"](t[sel],np.array([x,-.051,z]),np.array([0.,1.,0.]))
        return (names[mi[ii[sel[k]]]],round(float(pt[1]),6)) if np.isfinite(dist) else (None,None)
    positions={r['label']:r for r in openings()}
    fascia={b['bay']:rect(b['black_fascia'],-.32).bounds[3] for b in DATA['bays']}
    tests=[]
    for label,rec in DIRECT.items():
        r=positions[label];l=r['left']-.006;h=r['right']+.006;zb=fascia[r['bay']]-.11;zt=r['bottom']-.304
        rw,rh=rec['rectification_px'];levels=[0,*rec['bed_centres_px'],rh]
        for i,course in enumerate(rec['courses']):
            row=(levels[i]+levels[i+1])/2;heads=course['visible_heads_px']
            if i:
                # Sample in the middle of a wide overlap of the units flanking
                # this horizontal joint, away from vertical perpends.
                up=rec['courses'][i-1]['visible_heads_px']
                cuts=sorted(set([0,rw,*heads,*up]));a,b=max(zip(cuts,cuts[1:]),key=lambda q:q[1]-q[0]);sx=(a+b)/2
                x=l+sx*(h-l)/rw;z=zt-levels[i]*(zt-zb)/rh
                tests.append((label,'bed',i,levels[i],normal_hit(x,z),normal_hit(x,z+.014)))
            for u in heads:
                x=l+u*(h-l)/rw;z=zt-row*(zt-zb)/rh
                tests.append((label,'head',i,u,normal_hit(x,z),normal_hit(x+.016,z)))
    joints=[]
    for label,kind,i,u,(base,depth),(side,face) in tests:
        gap=round(depth-face,6) if depth is not None and face is not None else None
        joints.append({'apron':label,'kind':kind,'course':i+1,'rectified_pixel':u,'bed_material':base,'adjacent_face':side,'relief_m':gap,'passed':base==BED and side in PALE and gap is not None and gap>.006})
    return {'mesh':asset,'street_photo_probes':photo_points,'directly_measured_joints':joints,'visible_photo_probes':sum(v['visible_pale']for v in photo_points),'passed_joints':sum(v['passed']for v in joints),'bed_joints':sum(v['kind']=='bed'for v in joints),'head_joints':sum(v['kind']=='head'for v in joints)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--project',type=Path,default=HERE.parents[3]);a=ap.parse_args()
    result=check(a.mesh,a.project);a.output.write_text(json.dumps(result,indent=1,ensure_ascii=False)+'\n')
    print('pale photo patches',result['visible_photo_probes'],'of',len(result['street_photo_probes']),
          'direct joints',result['passed_joints'],'of',len(result['directly_measured_joints']))
