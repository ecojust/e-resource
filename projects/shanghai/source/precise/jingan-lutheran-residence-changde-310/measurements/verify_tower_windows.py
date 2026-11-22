"""Check the first opaque triangle at the measured openings in a supplied binary GLB."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from paired_tower_windows import BRICK,RECESS,LIP,KEY,SILL,TIMBER,BEAD,GLASS,LIGHT,FAN,openings
from changde_photo_plane import camera_matrix
from glb_triangles import SerialScene

def check(asset):
    scene=SerialScene(asset);controls=[]
    def ray(label,origin,direction,limit,expected,**info):
        hit=scene.ray(origin,direction,limit)
        material=hit['material'] if hit else None
        controls.append(dict(label=label,expected=expected,first_material=material,passed=material in expected,**info))
    def front(label,x,z,expected):
        ray(label,[x,-1.,z],[0,1,0],2.,expected,world_xz=[x,z])
    for w in openings():
        name=w['key'];l,r=w['left'],w['right'];x=.5*(l+r)
        z=w['spring'];rise=w['top']-z;rad=(r-l)/2;rx=w['outer_radius_x'];rz=w['outer_crown_z']-z
        for i,theta in enumerate(np.linspace(.19,np.pi-.19,13)):
            u=np.cos(theta);v=np.sin(theta)
            front(name+' / arch soffit lip '+str(i),x+(rad+.021)*u,z+(rise+.024)*v,[LIP])
            front(name+' / red arch face '+str(i),x+(.66*rad+.34*rx)*u,z+(.66*rise+.34*rz)*v,[BRICK,LIP,KEY])
        for i,f in enumerate((.11,.30,.52,.69,.89)):
            h=w['bottom']+(w['fan_base_z']-w['bottom'])*f
            front(name+' / left stile '+str(i),l+.023,h,[TIMBER])
            front(name+' / right stile '+str(i),r-.023,h,[TIMBER])
            front(name+' / meeting stile '+str(i),x,h,[TIMBER])
        for i,level in enumerate(w['timber_transoms_z']):
            front(name+' / small rail '+str(i),x+rad*.40,level,[TIMBER,BEAD])
        bounds=sorted([w['bottom']+.065,w['fan_base_z']-.056,*w['timber_transoms_z']])
        for j,(a,b) in enumerate(zip(bounds,bounds[1:])):
            for side in (-1,1):front(name+' / glass '+str((j,side)),x+side*rad*.49,(a+b)/2,[GLASS,LIGHT])
        for i,f in enumerate((-.78,-.25,.22,.8)):front(name+' / stone sill '+str(i),x+rad*f,w['bottom']-.047,[SILL])
        for i,t in enumerate((.13,.39,.59)):
            front(name+' / fanlight '+str(i),x+rad*.12,z+rise*t,[FAN,BEAD])
        front(name+' / crown keystone',x,w['outer_crown_z']+.011,[KEY])
        h=.5*(w['bottom']+w['spring'])
        for i,side in enumerate((-1,1)):
            ray(name+' / return on the clear jamb '+str(i),[x,.16,h],[side,0,0],2.,[RECESS])
        ray(name+' / sill return behind the front edge',[x,.21,w['bottom']+.18],[0,0,-1],.30,[SILL])
        ray(name+' / shaded intrados inside the arch',[x,.19,z+.06],[0,0,1],1.,[RECESS])
        # Independent frontal-photograph controls through the complete scene.
    samples=[(448,47,KEY),(507,46,KEY),(433,152,SILL),(503,153,SILL),
             (446,98,TIMBER),(506.8,100,TIMBER),(439,121,GLASS),(516,139,GLASS),
             (449,246,KEY),(510,246,KEY),(449,286,TIMBER),(509,294,TIMBER),
             (438,319,GLASS),(520,348,GLASS),(439,377,SILL),(517,377,SILL)]
    P=camera_matrix('gao-09');c=-np.linalg.solve(P[:,:3],P[:,3])
    for u,v,expected in samples:
        exp=[GLASS,LIGHT] if expected==GLASS else [expected]
        ray('Gao front photograph / '+str((u,v)),c,np.linalg.solve(P[:,:3],[u,v,1.]),210,exp,original_px=[u,v],image='gao-09')
    return dict(**scene.asset,method='Unfiltered first triangle of the supplied GLB; original-photo rays retain their native pixel coordinates.',count=len(controls),passed=all(c['passed'] for c in controls),checks=controls)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('asset',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();r=check(args.asset);args.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
    bad=[(c['label'],c['first_material']) for c in r['checks'] if not c['passed']]
    print(f"{r['count']-len(bad)}/{r['count']}",bad);raise SystemExit(bool(bad))
