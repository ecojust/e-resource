"""Export closed editable solids and check first material hits at native photo points."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'source'), str(HERE.parents[1]/'hongkou-general-post-office/source/common'),
                str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from photo_architecture import Builder
from glb_triangles import SerialScene
from lane_head import add_lane_head, native_xz, PALETTE, FIELD, CAP, ORNAMENT


def export(mesh, low):
    builder = Builder(PALETTE)
    add_lane_head(builder, low)
    for part in builder.parts:
        v = np.array(part['vertices'])
        f = np.array(part['triangles'])
        edges = Counter((a,b) for face in f for a,b in zip(face, np.roll(face,-1)))
        if any(n != 1 or edges[b,a] != 1 for (a,b),n in edges.items()):
            raise ValueError('Unpaired edge in '+part['label'])
        t = (v - np.mean(v,axis=0))[f]
        if np.sum(t[:,0]*np.cross(t[:,1],t[:,2])) <= 0:
            raise ValueError('Normal direction in '+part['label'])
    builder.save(mesh,{'name':'South lane lintel with paired low peaks and raised scrolls'})
    return {'objects':len(builder.parts),'triangles':sum(len(p['triangles']) for p in builder.parts),
            'closed_positive_volume':True}


def check(mesh):
    scene = SerialScene(mesh)
    hits = []
    def test(uv, material, part):
        x,z = native_xz(uv)
        hit = scene.ray([x,-.8,z],[0,1,0],.9)
        actual = None if hit is None else hit['material']
        hits.append({'reference':part,'native_uv':uv,'xz_m':[round(x,4),round(z,4)],
                     'expected':material,'first':actual,'passed':actual==material})
    for u in [2492,2530,2570,2590]:
        for v in [2188,2210,2233]:
            test([u,v],CAP,'South pale strip')
        for v in [2198,2221,2244]:
            test([u,v],FIELD,'South gaps between strips')
    for u in [3061,3097,3130,3162]:
        for v in [2200,2222,2244]:
            test([u,v],CAP,'North pale strip')
        for v in [2210,2233,2254]:
            test([u,v],FIELD,'North gaps between strips')
    for u in [2485,2540,2660,2765,2850,2910,3050,3170]:
        v = 2255+(u-2468)*12/716
        test([u,v],CAP,'Continuous bottom lip')
    for u,v in [(2640,2118),(2700,2096),(2794,2060),(2828,2079),(2863,2060),(2940,2098),(3010,2129)]:
        test([u,v],CAP,'Crown edge')
    for u,v in [(2820,2144),(2827,2144),(2831,2144),(2810,2154),(2818,2154),(2827,2154),
                (2836,2154),(2843,2154),(2852,2154),(2804,2162),(2815,2162),(2827,2162),
                (2833,2162),(2839,2162),(2850,2162),(2818,2170),(2827,2170),(2837,2170),
                (2822,2178),(2832,2178),(2827,2187)]:
        test([u,v],ORNAMENT,'Pale crest on original artwork')
    for u,v in [(2806,2154),(2815,2154),(2821,2154),(2833,2154),(2839,2154),(2848,2154),
                (2809,2162),(2818,2162),(2824,2162),(2830,2162),(2836,2162),(2844,2162),
                (2821,2170),(2832,2170),(2810,2187),(2840,2187)]:
        test([u,v],FIELD,'Exposed field between scrolls')
    for u,v in [(2640,2100),(2700,2081),(2828,2060),(2940,2080),(3020,2120),
                (2550,2283),(2750,2290),(3030,2290)]:
        test([u,v],None,'Clear silhouette at front of lintel')
    return {'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'rays':len(hits),
            'passed':all(h['passed'] for h in hits),'hits':hits}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('--export',choices=['full','lod'])
    args=parser.parse_args()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    stats=export(args.mesh,args.export=='lod') if args.export else None
    data=check(args.mesh)
    if stats:data.update(stats)
    args.report.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
    print({k:v for k,v in data.items() if k!='hits'})
    for h in data['hits']:
        if not h['passed']:print(h['native_uv'],h['reference'],h['first'])
    raise SystemExit(0 if data['passed'] else 1)
