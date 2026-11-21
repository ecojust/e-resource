"""Independently trace the Savoy street galleries, faceted bay and grey street wall."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-savoy-apartments-street-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    import math
    rows=[]
    def probe(label,origin,direction,materials,lo,hi,length=65):
        hit=scene.ray(origin,direction,length)
        ok=hit is None if materials is None else hit is not None and hit['material'] in materials and lo<=hit['distance_m']<=hi
        rows.append(dict(label=label,origin=origin,direction=direction,expected_materials=materials,distance_bounds_m=[lo,hi],actual=hit,passed=ok))
    glass=['grey blue glass','painted steel']
    # Corners, two orthogonal casement rows, parapets and visible strings are
    # measured from the street. Angled ends remain behind the chamfer plane.
    for name,base,end,sign in [('Changshu',(5.0305363,0),(33.9747491,38.3314848),1),('Yanqing',(-5.0305363,0),(-38.1624596,23.1245058),-1)]:
        x0,y0=base;dx,dy=end[0]-x0,end[1]-y0;length=math.hypot(dx,dy);dx/=length;dy/=length;nx,ny=sign*dy,-sign*dx
        def shoot(where,frac,z,materials,lo,hi,length_limit=65):
            origin=[x0+frac*length*dx+nx*4,y0+frac*length*dy+ny*4,z]
            probe(name+' '+where,origin,[-nx,-ny,0],materials,lo,hi,length_limit)
        for j in range(7):
            ground=3.66+j*3.16
            for u in (.084,.463,.562,.920):
                shoot('seven casement tiers',u,ground+1.22,glass,4.10,4.20)
            for u in (.264,.730):
                shoot('faceted parapet front',u+.024,ground+.55,['pebbled cement'],3.25 if j<6 else 3.64,3.31 if j<6 else 3.71)
                shoot('straight landing rim',u-.023,ground+1.085,['ivory moulding'],3.21 if j<6 else 3.60,3.29 if j<6 else 3.68)
                shoot('diagonal stair string',u,ground+1.74,['ivory moulding'],4.89,5.25)
                shoot('recess behind landing',u+.095,ground+1.57,['sheltered stucco'],6.40,6.53)
            if j:
                shoot('horizontal projecting sill case',.463,ground+.18,['ribbed metal'],3.58,3.72)
        shoot('projecting light cornice',.494,26.01,['ivory moulding'],3.32,3.41)
        shoot('ground shop glazing',.446,1.52,glass,4.22,4.33)
    for j in range(7):
        z=3.66+3.16*j+1.29
        for sign in [-1,1]:
            probe('chamfer flanking casements',[3.9*sign,-4,z],[0,1,0],glass,4.10,4.21)
        probe('faceted or flat central casement',[.22,-4,z],[0,1,0],glass,3.22 if j in range(1,6) else 4.10,3.31 if j in range(1,6) else 4.21)
    for x in [-2.09,2.09]:
        probe('shell relief beside attic window',[x,-4,24.57],[0,1,0],['ivory moulding'],3.85,3.98)
    for x,y in [(0,-3),(0,10),(-25,8),(25,45)]:
        probe('empty outside the authored street shell',[x,y,36],[0,0,-1],None,0,0,37)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
