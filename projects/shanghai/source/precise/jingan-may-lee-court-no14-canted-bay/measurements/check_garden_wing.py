"""Probe unfiltered first surfaces on the three garden-wing windows and eaves."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(HERE.parent/'source'))
from glb_triangles import SerialScene
import garden_main_corner as g

# Native 690 x 821 photograph, origin top left. A narrow rail or bead can be
# about one source pixel wide. Keep its exact first material and any local
# tolerance together in the output, also when an overlapping rail wins a ray.
NATIVE={
    'brick':[(136,314),(199,319),(134,457),(198,458),(136,614),(197,610),(165,366),(172,539)],
    'glass':[(161,282),(176,253),(162,297),(179,272),(163,278),(181,283),
             (160,441),(169,434),(179,442),(163,470),(173,455),(182,461),
             (160,606),(168,602),(180,599),(159,622),(170,624),(183,634)],
    'stone':[(151,289),(151,302),(151,317),(151,443),(151,460),(153,478),
             (148,597),(150,616),(151,636)],
    'ledge':[(159,324),(174,310),(180,303),(158,496),(176,486)],
    'metal':[(168,287),(176,280),(164,307),(170,450),(175,470),(169,614),(178,633)],
    'soffit':[(242,71),(261,83),(276,94),(201,118),(187,140),(162,178)],
    'fascia':[(245,57),(262,68),(270,76)],
    'dark_edge':[(241,34),(252,43),(272,57),(207,80),(171,138)],
    'pale_inset':[(286,79),(291,82),(134,194),(136,191)]}
def label(mat):
    if mat is None:return None
    if mat==g.garden_bay.BRICK:return 'brick'
    if mat in g.GLASS:return 'glass'
    if mat in (g.STONE,g.REVEAL):return 'stone'
    if mat==g.LEDGE:return 'ledge'
    if mat in (g.METAL,g.HEAVY):return 'metal'
    return {g.UNDER:'soffit',g.BROWN:'fascia',g.DARK:'dark_edge',g.PANEL:'pale_inset'}.get(mat,mat)
def inspect(path):
    scene=SerialScene(path)
    projection=np.array(json.loads((HERE/'garden-corner-camera.json').read_text())['main_corner_projection'])
    inv=np.linalg.inv(projection[:,:3]);origin=-inv@projection[:,3]
    def cast(start,dir):
        hit=scene.ray(np.asarray(start),np.asarray(dir),100)
        return hit['material'] if hit else None
    physical=[]
    for name,a,c,lo,hi,rails,bars in g.WINDOWS:
        us=[a+.130,*bars,c-.130];zs=[lo+.135,*rails,hi-.120]
        def probe(y,z,expect,tag):
            mat=cast([g.X-.33,y,z],[1,0,0])
            physical.append(dict(storey=name,sample=tag,y_m=round(y,4),z_m=round(z,4),expected=expect,
                                 material=mat,matched=(label(mat)==expect)))
        for col,(left,right) in enumerate(zip(us,us[1:])):
            for row,(base,head) in enumerate(zip(zs,zs[1:])):
                probe((left+right)/2,(base+head)/2,'glass',f'pane-{col+1}-{row+1}')
        for u in bars:
            for base,head in zip(zs,zs[1:]):probe(u,(base+head)/2,'metal','vertical bar')
        for z in rails:
            for near,far in zip(us,us[1:]):probe((near+far)/2,z,'metal','horizontal rail')
        for yy in [a+.040,c-.040]:
            for z in [(lo+hi)/2,lo+.27,hi-.28]:probe(yy,z,'stone','stone jamb')
        for u in [(a+c)/2,a+.14,c-.14]:
            probe(u,lo+.052,'ledge','projecting stone stool')
            probe(u,hi-.04,'stone','head')
    readings=[]
    for expected,points in NATIVE.items():
        for u,v in points:
            direct=cast(origin,inv@[u,v,1.]);match=None
            limit=2 if expected in ('metal','ledge','fascia','pale_inset') else 1
            offsets=sorted(((x,y) for x in range(-limit,limit+1) for y in range(-limit,limit+1)
                            if x*x+y*y<=limit*limit),key=lambda p:p[0]**2+p[1]**2)
            for dx,dy in offsets:
                found=direct if dx==dy==0 else cast(origin,inv@[u+dx,v+dy,1.])
                if label(found)==expected:match=[dx,dy];break
            readings.append(dict(pixel=[u,v],expected=expected,first_material=direct,matched_offset=match))
    return {'asset':scene.asset,'physical_samples':len(physical),'physical_pass':sum(r['matched'] for r in physical),
            'native_samples':len(readings),'native_direct':sum(r['matched_offset']==[0,0] for r in readings),
            'native_with_tolerance':sum(r['matched_offset'] is not None for r in readings),
            'physical':physical,'photographic':readings}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('glb',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();r=inspect(args.glb)
    args.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    print({k:v for k,v in r.items() if k not in ('physical','photographic')})
