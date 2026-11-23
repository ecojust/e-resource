"""Check the pierced north facade through actual garden GLB triangles."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parent/'source'))
sys.path.insert(0,str(M.parents[3]/'tools'))
sys.path.insert(0,str(M.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene
from nine_north_windows import openings, GLASS, WOOD, BEAD, EDGE, PLASTER
from check_hongji_roofs import map_frame

# Points well within actually visible glass, head layers or frames in the two
# unaltered photographs. The photographs' independent square-pixel solutions
# are preserved even where foreground shrubs or the plane fit displace a hit.
PIXELS={
 '20':{'glass':[(479,272),(497,268),(480,320),(495,317),(463,449),(501,444),
                 (713,269),(742,283),(716,439),(399,359),(222,351)],
       'surround':[(481,244),(483,348),(470,428),(733,322),(725,420)],
       'frame':[(490,292),(485,296)]},
 '22':{'glass':[(402,346),(435,349),(404,403),(437,438),(403,621),(450,632),
                 (227,347),(224,407),(581,479)],
       'surround':[(418,309),(429,463),(413,590),(222,448),(582,522)],
       'frame':[(421,354),(402,383)]}}
EXPECTED={'glass':set(GLASS),'frame':{BEAD,WOOD},'surround':{EDGE,PLASTER}}

def report(mesh,local):
    scene=SerialScene(mesh);offset,basis=map_frame(9)
    def ray(o,d,allowed):
        o=np.array(o);d=np.array(d);d=d/np.linalg.norm(d)
        if not local:o,d=offset+basis@o,basis@d
        hit=scene.ray(o,d,90.)
        return {'matched':bool(hit and hit['material']in allowed),
                'first_material':hit['material']if hit else None}
    per=[]
    for win in openings({}):
        a=np.array(win['a']);c=np.array(win['c']);u=c-a
        w=np.linalg.norm(u);u=u/w;n=np.array([u[1],-u[0],0.])
        z0,z1=win['low'],win['high'];h=z1-z0
        for f,v,kind in [(.23,.17,'glass'),(.76,.40,'glass'),(.22,.76,'glass'),(.74,.77,'glass'),
                         (.50,.60,'frame'),(.028/w,.40,'frame'),(.5,1+.07/h,'surround')]:
            xyz=np.r_[a+f*(c-a),z0+v*h]
            per.append({'id':win['id'],'target':kind,'local_xyz':xyz.round(5).tolist(),
                        **ray(xyz+n*.42,-n,EXPECTED[kind])})
    evidence=json.loads((M/'nine-north-windows-and-stepped-gables.json').read_bytes())
    photo=[]
    for name,classes in PIXELS.items():
        P=np.array(evidence['views'][name]['P']);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
        for kind,points in classes.items():
            for uv in points:
                result=ray(eye,inv@np.r_[uv,1.],EXPECTED[kind])
                first_offset=[0,0] if result['matched'] else None
                if first_offset is None:
                    # Sample a small fixed image neighbourhood, spanning the
                    # observed 1–7 px errors of the unaltered camera fits.
                    for r in (2,4,6,8):
                        for dx,dy in ((r,0),(-r,0),(0,r),(0,-r)):
                            if ray(eye,inv@[uv[0]+dx,uv[1]+dy,1.],EXPECTED[kind])['matched']:
                                first_offset=[dx,dy]
                                break
                        if first_offset is not None:break
                photo.append({'source':name,'native_pixel':uv,'target':kind,
                              'nearest_tested_offset_px':first_offset,**result})
    return {'mesh':scene.asset,'fitted_source_sha256':hashlib.sha256(
        (M/'nine-north-windows-and-stepped-gables.json').read_bytes()).hexdigest(),
        'photo_within_eight_pixels':sum(v['nearest_tested_offset_px'] is not None for v in photo),
        'openings':openings({}),'wall_normal_tests':per,'photo_pixels':photo,
        'summary':{k:[sum(v['matched'] for v in rows),len(rows)]
                   for k,rows in [('wall_normal',per),('registered_photo',photo)]}}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path)
    ap.add_argument('--local',action='store_true');a=ap.parse_args()
    data=report(a.mesh,a.local)
    a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(data['summary'])
