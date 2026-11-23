"""Trace manually read points in three published photographs against the actual delivered mesh."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.extend([str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')])
from curved_veranda import CAP,IRON,LINING,PLASTER,RIDGE,SOFFIT,TILE,TILE_DARK,TILE_WARM,TILE_LIGHT,WOOD,settings
from glb_triangles import SerialScene
materials={'clay':[TILE,TILE_LIGHT,TILE_WARM,TILE_DARK,RIDGE],'timber':[WOOD],'plaster':[PLASTER],'soffit':[SOFFIT],'cap':[CAP],'iron':[IRON],'door':[LINING]}
POINTS={
'sina-37':[
 ('hip tile west',205,65,'clay'),('hip tile east',260,57,'clay'),('hip centre',237,66,'clay'),
 ('left dark post',174,139,'timber'),('right dark post',307,139,'timber'),
 ('outer west diagonal',155,175,'timber'),('outer east diagonal',328,159,'timber'),
 ('outer west plaster infill',146,182,'plaster'),('outer east plaster infill',318,163,'plaster'),
 ('left raised wing',198,174,'plaster'),('right raised wing',280,169,'plaster'),
 ('panel below the ironwork',237,184,'plaster'),('underside of the balcony',236,207,'soffit'),
 ('west brick coping',198,150,'cap'),('east brick coping',278,147,'cap'),
 ('left shadowed doorway leaf',212,138,'door'),('right shadowed doorway leaf',260,138,'door')],
'paper-25':[
 ('upper hip tile',333,23,'clay'),('hip lower left',314,37,'clay'),('hip lower right',362,40,'clay'),
 ('outer west infill',280,98,'plaster'),('outer east infill',391,109,'plaster'),
 ('west post above the crossing',299,81,'timber'),('east main post at crossing',374,89,'timber'),
 ('west plaster shoulder',315,103,'plaster'),('east plaster shoulder',359,105,'plaster'),
 ('panel below the grille',336,113,'plaster'),('shaded soffit',336,125,'soffit')],
'sina-35':[
 ('upper hip tile',114,44,'clay'),('side pitch',206,53,'clay'),('side tile rows',211,67,'clay'),
 ('left timber sill',78,201,'timber'),('left post',91,159,'timber'),('left side white infill',72,183,'plaster'),
 ('near plaster parapet',173,150,'plaster'),('curved sill below ironwork',139,172,'plaster'),
 ('underside centre',142,199,'soffit'),('left brick coping',106,142,'cap'),('right brick coping',170,127,'cap')]
}

def camera_in_metres(station,p):
    width=p['post_span']
    origin=np.array([p['center_x'],p['front_y'],p['deck_z']])
    P=np.array(station['P']); E=-np.linalg.solve(P[:,:3],P[:,3])
    transform=np.eye(4);transform[:3,:3]/=width;transform[:3,3]=-origin/width
    return P@transform,origin+width*E

def check(mesh,layout):
    p=settings(layout);d=json.loads((HERE/'curved-veranda-folded-roof.json').read_text())
    scene=SerialScene(mesh);out=[]
    for name in POINTS:
        station=d['stations'][name]
        P,eye=camera_in_metres(station,p)
        for label,u,v,mat in POINTS[name]:
            direction=np.linalg.solve(P[:,:3],[u,v,1])
            direction/=np.linalg.norm(direction)
            hit=scene.ray(eye,direction,100)
            found=hit['material'] if hit else None
            match=found in materials[mat]; nearest=[0,0] if match else None
            if not match:
                offsets=sorted(((i,j)for i in range(-3,4)for j in range(-3,4) if 0<i*i+j*j<=9),key=lambda t:t[0]**2+t[1]**2)
                for dx,dy in offsets:
                    ray=np.linalg.solve(P[:,:3],[u+dx,v+dy,1]);ray/=np.linalg.norm(ray)
                    near=scene.ray(eye,ray,100)
                    if near and near['material'] in materials[mat]:
                        nearest=[dx,dy];break
            out.append(dict(photo=name,label=label,pixel=[u,v],expected_materials=materials[mat],
                            observed=found,local_hit=hit['point_enu_m'] if hit else None,match=match,
                            nearest_matching_offset_px=nearest))
    return dict(file=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),layout=p,
                matched=sum(x['match'] for x in out),samples=len(out),measurements=out)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('out',type=Path)
    parser.add_argument('--layout',type=Path);a=parser.parse_args()
    m=check(a.mesh,json.loads(a.layout.read_text()) if a.layout else None)
    a.out.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print(m['matched'],m['samples'])
