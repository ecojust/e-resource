"""Check the centre light of the photographed window wall and independent sight lines through the hall."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from auditorium import LEFT, RIGHT, WINDOW_CENTRES, WINDOW_HEIGHT_SCALE, CLEAR, CYAN, RED, GOLD, LEAD, PLASTER, FLOOR, OAK, SEAT
HELPER=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
# Centre bay of the 507 x 380 district broadside photograph. Coordinates in working pixels.
# The window plane is registered, not the unmeasured focal length or interior viewpoint.
UV=[(217,226),(314,226),(218,65),(314,65)]
CHECKS={LEAD:[(265,44),(243,136),(290,136)], CYAN:[(238,122),(289,119)],
        CLEAR:[(244,145),(287,154),(241,166)], GOLD:[(239,218),(286,218)],
        PLASTER:[(263,105),(264,176)], RED:[(224,191),(308,191)]}

def homography():
    centre=WINDOW_CENTRES[1]
    yz=[(centre-1.63,1.19),(centre+1.63,1.19),(centre-1.63,6.15),(centre+1.63,6.15)]
    mat=[];target=[]
    for (u,v),(y,z) in zip(UV,yz):
        mat += [[u,v,1,0,0,0,-u*y,-v*y],[0,0,0,u,v,1,-u*z,-v*z]]
        target.extend([y,1.19+(z-1.19)*WINDOW_HEIGHT_SCALE])
    return np.r_[np.linalg.solve(mat,target),1].reshape(3,3)


def inspect(mesh):
    scene=runpy.run_path(str(HELPER))['SerialScene'](mesh)
    h=homography()
    def hit(origin,dir,maxdist):
        direction=np.asarray(dir,dtype=float);direction/=np.linalg.norm(direction)
        rec=scene.ray(np.asarray(origin,dtype=float),direction,maxdist)
        return rec['material'] if rec else None
    def window_ray(u,v):
        v=h@np.array([u,v,1.])
        y,z=v[:2]/v[2]
        return hit((LEFT+1,y,z),(-1,0,0),2)
    rays=[]
    for mat,uvs in CHECKS.items():
        for u,v in uvs:
            direct=window_ray(u,v);nearest=None
            for d,ix,iy in sorted((a*a+b*b,a,b)for a in range(-4,5)for b in range(-4,5)if a*a+b*b<=16):
                if window_ray(u+ix,v+iy)==mat:
                    nearest=round(float(d)**.5,3);break
            rays.append(dict(uv=[u,v],material=mat,first_material=direct,nearest_px=nearest))
    fixtures=[
        ('west back rectangular jewel',(LEFT+1,26.37-.66-.38,1.52),(-1,0,0),2,CYAN),
        ('east gallery window jewel',(RIGHT-1,26.37+.66+.38,1.52),(1,0,0),2,CYAN),
        ('balcony panel front',(0,27.0,4.53),(0,-1,0),4,PLASTER),
        ('left bay oculus',(LEFT+1,29.785,1.19+(6.91-1.19)*WINDOW_HEIGHT_SCALE),(-1,0,0),2,LEAD),
        ('opposite bay roundel',(RIGHT-1,41.7-.81+.10,1.19+(4.27-1.19)*WINDOW_HEIGHT_SCALE),(1,0,0),2,CYAN),
        ('seat backs',(-5.0,30.4,.65),(0,1,0),3,SEAT),
        ('stage apron',(0,43,.48),(0,1,0),6,OAK),
        ('coffer soffit',(-3.,30.,3.50),(0,0,1),7,PLASTER),
        ('central aisle floor',(0,31.,1.56),(0,0,-1),2,FLOOR),
        ('clear audience centre aisle',(0,14.,1.60),(0,1,0),31,None)]
    architecture=[]
    for label,o,d,reach,expected in fixtures:
        seen=hit(o,d,reach);architecture.append(dict(target=label,origin=o,direction=d,reach=reach,expected=expected,hit=seen,passed=seen==expected))
    return dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),photo='https://www.shcn.gov.cn/col6991/20221017/1223835.html',
                frame=[507,380],method='planar registration of one bay; local perpendicular rays from hall interior',controls=UV,
                samples=rays,direct=sum(a['first_material']==a['material']for a in rays),within_four=sum(a['nearest_px'] is not None for a in rays),architectural_sections=architecture)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();result=inspect(a.mesh);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['direct'],result['within_four'],len(result['samples']),[(r['target'],r['hit'])for r in result['architectural_sections']if not r['passed']])
