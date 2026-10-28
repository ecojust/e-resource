#!/usr/bin/env python3
"""Find overlapping upward masonry/paving/coping triangles in actual GLBs."""
from pathlib import Path
import argparse,hashlib,json,struct
from collections import defaultdict
import numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parent.parent
MATERIALS={'original grey brick','worn paving','worn coping'}


def inspect(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);binary=raw[28+n:]
    def a(index):
        ac=d['accessors'][index];v=d['bufferViews'][ac['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[ac['componentType']]
        cols={'SCALAR':1,'VEC3':3,'VEC2':2}[ac['type']]
        return np.frombuffer(binary,dtype=dt,count=ac['count']*cols,offset=v.get('byteOffset',0)+ac.get('byteOffset',0)).reshape(-1,cols)
    groups=defaultdict(list)
    for mi,m in enumerate(d['meshes']):
        for pi,p in enumerate(m['primitives']):
            name=d['materials'][p['material']]['name']
            if name not in MATERIALS:continue
            positions=a(p['attributes']['POSITION']).astype(float);indices=a(p['indices']).reshape(-1,3)
            for ti,tri in enumerate(positions[indices]):
                normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);length=np.linalg.norm(normal)
                if length<1e-12 or normal[1]/length<.99999 or np.ptp(tri[:,1])>1e-6:continue
                shape=Polygon(tri[:,[0,2]])
                if shape.area<1e-9:continue
                key=round(float(tri[0,1]),5)
                groups[key].append((shape,{'mesh':mi,'primitive':pi,'triangle':ti,'material':name}))
    overlaps=[];max_area=0.;tested=0
    for height,items in groups.items():
        polygons=[p[0] for p in items];tree=STRtree(polygons)
        for i,poly in enumerate(polygons):
            for j in tree.query(poly,predicate='intersects'):
                j=int(j)
                if j<=i:continue
                tested+=1;area=poly.intersection(polygons[j]).area;max_area=max(max_area,area)
                if area>1e-5:
                    overlaps.append({'height_m':height,'overlap_area_m2':area,'a':items[i][1],'b':items[j][1]})
    return {'file':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'selected_materials':sorted(MATERIALS),
            'horizontal_upward_triangles':sum(len(v) for v in groups.values()),'height_groups':len(groups),'candidate_triangle_pairs':tested,
            'overlap_area_tolerance_m2':1e-5,'largest_pair_overlap_m2':max_area,'overlaps_above_tolerance':len(overlaps),'overlap_examples':overlaps[:20],
            'scope':'Actual serialized FLOAT32 upward horizontal masonry/paving/coping faces only; does not assert absence of all internal, sloped or other-material overlaps.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline',type=Path);args=parser.parse_args()
    result={'schema':'jinshan-horizontal-surface-ownership-v1','assets':[]}
    for name in ['jinshanwei-gatehouse-raw.glb','jinshanwei-gatehouse-lod-source.glb']:
        r=inspect(ROOT/'exports'/name);result['assets'].append(r)
    if args.baseline:
        result['baseline']=inspect(args.baseline/'exports/jinshanwei-gatehouse-raw.glb')
    result['passed']=all(r['overlaps_above_tolerance']==0 for r in result['assets'])
    if args.baseline:result['regression_demonstrated']=result['baseline']['overlaps_above_tolerance']>0 and result['passed']
    (ROOT/'review/horizontal-surface-ownership.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'assets':[{'file':r['file'],'overlaps':r['overlaps_above_tolerance'],'max_pair_area':r['largest_pair_overlap_m2']} for r in result['assets']],
                      'baseline_overlaps':result.get('baseline',{}).get('overlaps_above_tolerance')}))
    if not result['passed']:raise SystemExit(1)
