#!/usr/bin/env python3
"""Independent v1/v2 construction invariance and vertical internal-face audit."""
from collections import Counter,defaultdict
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import numpy as np
from shapely.geometry import Polygon

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'xuhui-wukang-129'
CHANGED={
 'A-left-gabled-front/continuous-open-wall','C-low-front-extension-estimate/continuous-open-wall',
 'D-low-entrance/continuous-open-wall','unphotographed-original-edge-2/continuous-open-wall',
 'unphotographed-original-edge-2/base-course','E-rounded-front-true-arch-wall','E-curved-gray-plinth',
 'ACF-single-union-front-with-original-openings'}


def target(part):
    return part['label'] in CHANGED or part['label'].startswith('D-visible-upper-')


def capture(root,name):
    with tempfile.TemporaryDirectory(prefix='wukang129-invariant-') as td:
        d=Path(td)/name
        shutil.copytree(root,d,ignore=shutil.ignore_patterns('output','native','__pycache__'))
        spec=importlib.util.spec_from_file_location(name,d/'build_model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        captured=[]
        old=m.Builder
        class Capture(old):
            def save(self,path,metadata=None):
                captured.extend(self.parts)
                pts=np.asarray([p for part in self.parts for p in part['vertices']]);g=pts[:,[0,2,1]]*[1,1,-1]
                return {'file':Path(path).name,'bytes':0,'sha256':'capture-only-no-export',
                        'triangles':sum(len(p['triangles']) for p in self.parts),'parts':len(self.parts),
                        'materials':len({p['material'] for p in self.parts}),
                        'bounds_glb':{'min':g.min(0).tolist(),'max':g.max(0).tolist()}}
        m.Builder=Capture
        # Actual exported model has its own full FLOAT32 structural check. This
        # audit captures construction arrays without exporting a second asset.
        m.check_parts=lambda b:{'passed':True,'scope':'capture only; see final raw structural report','parts':[]}
        m.build(d/'output')
        parameters=json.loads((d/'calibration-model.json').read_text())
        return captured,parameters


def part_sha(part,precision='<f8'):
    h=hashlib.sha256((part['label']+'\0'+part['material']).encode())
    h.update(np.asarray(part['vertices'],dtype=precision).tobytes());h.update(np.asarray(part['triangles'],dtype='<u4').tobytes())
    return h.hexdigest()


def contacts(parts):
    groups=defaultdict(list)
    for partno,part in enumerate(parts):
        if part['material']!='cream plaster':continue
        v=np.asarray(part['vertices'],float)
        for ti,tri in enumerate(part['triangles']):
            p=v[list(tri)];n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
            if abs(n[2])>1e-8:continue
            canon=n.copy()
            if canon[0]<-1e-8 or abs(canon[0])<=1e-8 and canon[1]<0:canon=-canon
            distance=float(canon@p[0]);key=(*np.round(canon,7),round(distance,6))
            tangent=np.array([-canon[1],canon[0],0.]);poly=Polygon(np.c_[p@tangent,p[:,2]])
            groups[key].append((partno,part['label'],ti,1 if n@canon>0 else -1,poly))
    found=[]
    for group in groups.values():
        positive=[x for x in group if x[3]>0];negative=[x for x in group if x[3]<0]
        for a in positive:
            for b in negative:
                area=a[4].intersection(b[4]).area
                if area>1e-8:found.append({'a':a[1],'b':b[1],'area_m2':area,'triangles':[a[2],b[2]]})
    return {'vertical_opposed_coplanar_contact_area_m2':sum(x['area_m2'] for x in found),'triangle_contact_pairs':len(found),'contacts':found}


def main():
    global BASE
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--baseline',type=Path,default=BASE);args=ap.parse_args();BASE=args.baseline.resolve()
    assert hashlib.sha256((BASE/'output/xuhui-wukang-129-raw.glb').read_bytes()).hexdigest()=='ebbe919f7289193947a21acf124113df76223ae853d6e22a464c64184276dd8d','Expected frozen v1 asset'
    before,old_parameters=capture(BASE,'before')
    after,new_parameters=capture(HERE,'after')
    untouched_before=[p for p in before if not target(p)];untouched_after=[p for p in after if not target(p)]
    exact64=Counter(part_sha(p) for p in untouched_before)==Counter(part_sha(p) for p in untouched_after)
    exact32=Counter(part_sha(p,'<f4') for p in untouched_before)==Counter(part_sha(p,'<f4') for p in untouched_after)
    assert exact64 and exact32,'Non-target part changed'
    assert old_parameters['windows']==new_parameters['windows'],'Window placement or inset changed'
    a,b=contacts(before),contacts(after)
    assert a['vertical_opposed_coplanar_contact_area_m2']>1
    assert b['vertical_opposed_coplanar_contact_area_m2']<1e-8,b
    for name in ['geometry-input.json','camera-2026.json','calibration/calibration-independent.json']:
        assert (BASE/name).read_bytes()==(HERE/name).read_bytes(),name
    for photo in (BASE/'references').glob('*original.jpg'):
        assert photo.read_bytes()==(HERE/'references'/photo.name).read_bytes()
    result={'schema':'wukang129-v2-revision-invariance-v1','passed':True,'baseline_raw_sha256':hashlib.sha256((BASE/'output/xuhui-wukang-129-raw.glb').read_bytes()).hexdigest(),
        'candidate_raw_sha256':hashlib.sha256((HERE/'output/xuhui-wukang-129-raw.glb').read_bytes()).hexdigest(),
        'untouched_parts_before':len(untouched_before),'untouched_parts_after':len(untouched_after),'untouched_float64_vertices_triangles_materials_exact':exact64,'untouched_float32_vertices_exact':exact32,
        'windows_exact':True,'window_count':len(new_parameters['windows']),'original_geometry_camera_calibration_photos_exact':True,
        'before_vertical_contacts':a,'after_vertical_contacts':b,
        'scope':'All generated cream-plaster vertical triangles, grouping coplanar opposing normals then measuring actual projected intersection. Horizontal floor/slab interfaces excluded. Unchanged parts compared as exact labeled multiset; no assertion that model is a single Boolean union.',
        'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/'output/revision-invariance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['passed','untouched_parts_before','windows_exact']},indent=2))
    print('vertical contacts',a['vertical_opposed_coplanar_contact_area_m2'],'->',b['vertical_opposed_coplanar_contact_area_m2'])


if __name__=='__main__':main()
