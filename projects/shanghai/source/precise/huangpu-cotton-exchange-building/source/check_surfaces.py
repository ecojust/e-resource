"""Probe the exchange windows, gate ironwork, lantern, roof, and the space outside its parcel."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-cotton-exchange-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    import numpy as np
    rows=[]
    def probe(label,origin,direction,material,depth,tol=.043):
        hit=scene.ray(list(origin),list(direction),50)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-depth)<tol)
        rows.append(dict(label=label,origin=list(origin),direction=list(direction),reference_depth_m=depth,
                         expected_material=material,hit=hit,passed=ok))
    from math import cos,sin,pi
    # Independent sightlines measured against the finished openings with the east and west street
    # wings checked separately. The intervals below are the south frontage/photo reading.
    for lo,hi,count in [(-20.05,-.95,4),(7.31,20.06,3)]:
        for i in range(count):
            x=lo+(i+.5)*(hi-lo)/count
            for z in [1.05,3.84,8.21,12.04,16.20]:
                probe('south street open casement',[x+.20,-2,z],[0,1,0],'green grey glazing',2.446)
            probe('deep south cornice below attic',[x+.18,-2,15.02],[0,1,0],'pale carved stone',2.12-(.055+.205))
    for x in [-.29,6.65]:
        for z in [8.32,12.31]:probe('narrow window beside oriel',[x+.13,-2,z],[0,1,0],'green grey glazing',1.957)
    for z in [8.33,12.30]:probe('canted central bay front glass',[3.38,-2,z],[0,1,0],'green grey glazing',1.318)
    probe('arched light below tympanum',[3.39,-2,16.81],[0,1,0],'green grey glazing',1.957)
    probe('inset door behind open grille',[3.18+.15,-2,2.94],[0,1,0],'entrance shadow',2.56)
    probe('central iron meeting bar',[3.18,-2,2.92],[0,1,0],'forged museum gate',2.437)
    probe('left half of round gate disc',[3.01,-2,1.44],[0,1,0],'aged gold inscription',2.348)
    probe('right half of round gate disc',[3.36,-2,1.44],[0,1,0],'aged gold inscription',2.348)
    probe('pillar and door soffit',[3.33,-2,4.40],[0,1,0],'pale carved stone',1.62+.42-.5)
    for x in [.65,5.71]:probe('Ionic portal shaft',[x,-2,2.05],[0,1,0],'pale carved stone',1.62-.292-.277,.044)
    for sample in json.loads((SOURCE/'museum-name-probes.json').read_bytes()):
        probe('museum inscription '+sample['char'],[3.18+sample['x'],-2,sample['z']],[0,1,0],'aged gold inscription',1.62-.235,.025)
    # Eight circular windows have real cut-outs, a recessed backing and a raised rim. The open
    # colonnade below is seen horizontally in between the regular upright positions.
    cx,cy=-20.05,4.5
    for i in range(8):
        a=(i+1)*pi/4;dx,dy=cos(a),sin(a);ap=2.81*cos(pi/8)
        probe('oculus inset in the dome drum',[cx+dx*5,cy+dy*5,25.97],[-dx,-dy,0],'entrance shadow',5-ap+.375,.045)
        probe('oculus surround',[cx+dx*5,cy+dy*5,26.51],[-dx,-dy,0],'pale carved stone',5-ap-.104,.041)
        probe('clear line through lantern at uncolumned azimuth',[cx+dx*4,cy+dy*4,22.21],[-dx,-dy,0],None,None)
        b=(i+.5)*pi/4;px,py=cos(b),sin(b)
        probe('gallery column outer surface',[cx+4.8*px,cy+4.8*py,22.21],[-px,-py,0],'pale carved stone',4.8-2.62-.241,.035)
    for x,y,z in [(6,5,19.12),(7,22,13.10),(15,29,13.10),(26,50,14.55),(32,59,19.12)]:
        probe('low trading-hall roof, northern court or upper terrace',[x,y,35],[0,0,-1],'dark pavilion roof',35-z)
    probe('flagstaff on dome centre',[cx,cy,35],[0,0,-1],'weathered sheet metal',35-31.69)
    for x,y in [(0,-2),(-27,4),(46,70),(45,16),(0,65)]:
        probe('road or air outside the original exchange',[x,y,35],[0,0,-1],None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(x['passed']for x in rows))


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
