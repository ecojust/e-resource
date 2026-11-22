"""Check unfiltered light paths through the photographed gate and its open centre."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'hongkou-general-post-office/source/common'),
              str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from photo_architecture import Builder
from lane_piers_gate import OBS, PALETTE, POST, SIDE, CAP, STEEL, EDGE, leaf, leaf_point, slots, add_lane_piers_gate


def export(path,low):
    b=Builder(PALETTE);add_lane_piers_gate(b,low)
    for part in b.parts:
        v=np.asarray(part['vertices']);f=np.asarray(part['triangles'])
        edges=Counter((a,c) for face in f for a,c in zip(face,np.roll(face,-1)))
        if any(n!=1 or edges[c,a]!=1 for (a,c),n in edges.items()):raise ValueError(part['label'])
        tri=(v-v.mean(axis=0))[f]
        if np.sum(tri[:,0]*np.cross(tri[:,1],tri[:,2]))<=0:raise ValueError(part['label'])
    b.save(path,{'name':'Visible piers and open green leaves, Rongkang south lane, 2017'})
    return {'parts':len(b.parts),'triangles':sum(len(p['triangles'])for p in b.parts),'positive_closed_solids':True}


def check(path):
    scene=SerialScene(path);rows=[]
    def cast(origin,direction,length,allow,name,control):
        hit=scene.ray(origin,direction,length)
        mat=hit['material'] if hit else None
        rows.append({'feature':name,'control':control,'first':mat,'allowed':allow,'passed':mat in allow})
    for i in [0,1]:
        outward=np.r_[leaf(i)[2],0.]
        def probe(u,t,approved,name):
            origin=leaf_point(i,u,t,.08)
            cast(origin,-outward,.14,approved,name,[i,u,t])
        for k in range(9):
            for u in [.19,.51,.79]:
                probe(u,.442+k*.0273,[None],'Through horizontal slot')
                probe(u,.456+k*.0273,[STEEL],'Metal between horizontal slots')
        for left,right in slots():
            for t in [.130,.395,.697,.965,.06]:
                probe((left+right)/2,t,[None],'Dark open end of lengthwise slot')
            for t in [.20,.76]:
                probe(left+(right-left)*.25,t,[STEEL],'Recessed blade behind slot')
        for u in [.029,.957]:
            for t in [.15,.24,.58,.74,.92]:
                probe(u,t,[STEEL,EDGE],'Solid outer stile')
    for x in [-1.82,-1.68,-1.52,1.69,1.80,1.92]:
        for z in [.44,1.37,2.17]:
            cast([x,-.60,z],[0,1,0],.85,[POST],'Upright on street',[x,z])
    for x in [-1.12,-.66,-.21,.36,.80,1.00]:
        for z in [.62,1.45,2.12]:
            cast([x,-.20,z],[0,1,0],2.35,[None],'Open central passage',[x,z])
    photo_tests={
       'original_full_matrix':[(POST,[(2470,2500),(2490,2610),(2510,2520),(2500,2400),
                    (3195,2500),(3210,2590),(3235,2790),(3165,2500),(3182,2740)]),
                    (CAP,[(2480,2361),(2510,2362)]),(STEEL,[(3011,2499),(3020,2607),(3016,2683),
                    (3024,2787),(3035,2855),(3080,2470),(3070,2592),(3085,2729),(3097,2813),(3099,2920)]),
                    (None,[(2644,2490),(2780,2510),(2800,2820)])],
       'september_800x890_matrix':[(STEEL,[(574,372),(590,430),(593,480),(603,532),(631,373)]),
                    (None,[(509,434),(531,483)])]}
    for key,groups in photo_tests.items():
        P=np.array(OBS['source_camera'][key])
        eye=np.linalg.solve(-P[:,:3],P[:,3])
        for mat,points in groups:
            for uv in points:
                direction=np.linalg.solve(P[:,:3],[*uv,1.])
                unit=direction/np.linalg.norm(direction)
                length=(2.18-eye[1])/unit[1] if mat is None else 27.
                allowed=[STEEL,EDGE] if mat==STEEL else [mat]
                cast(eye,unit,length,allowed,'Native photograph '+key,list(uv))
    return {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'test_count':len(rows),
            'native_photo_samples':sum(len(points)for group in photo_tests.values()for _,points in group),
            'unfiltered':True,'passed':all(v['passed']for v in rows),'tests':rows,
            'two_unclassified_native_points':'September (555,360) and (645,454) lie in the dark grating, whose bars and perforations cannot be distinguished there. In the first unfiltered render both rays pass through.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('report',type=Path)
    ap.add_argument('--export',choices=['full','lod']);a=ap.parse_args()
    info=export(a.mesh,a.export=='lod') if a.export else {}
    result={**info,**check(a.mesh)}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=1,ensure_ascii=False)+'\n')
    print({k:v for k,v in result.items()if k not in ('tests','two_unclassified_native_points')})
    for t in result['tests']:
        if not t['passed']:print(t)
    raise SystemExit(0 if result['passed'] else 1)
