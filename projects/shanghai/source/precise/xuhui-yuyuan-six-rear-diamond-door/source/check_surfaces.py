"""Check the signed glazed door surfaces and open passage."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-yuyuan-six-rear-diamond-door'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




"""Test the oak boards, their rebates, the glass diamond and its photographed iron grille."""
def test(scene):
    rows=[]
    def cast(label,origin,direction,extent,material=None,distance=None,tolerance=.0025):
        hit=scene.ray(list(origin),list(direction),extent)
        ok=(hit is None) if material is None else (hit is not None and hit['material'] in material and abs(hit['distance_m']-distance)<=tolerance)
        rows.append(dict(check=label,origin=origin,direction=direction,max_length=extent,allowed_materials=sorted(material or []),expected_distance_m=distance,tolerance_m=tolerance,hit=hit,passed=bool(ok)))
    def from_front(label,x,z,mat,front):
        cast(label,(x,-.6,z),(0,1,0),.8,mat,.6-front)
    for x in (-.425,-.211,.071,.30,.435):
        for z in (.23,.32,.403):from_front('Solid bottom rail',x,z,{'painted teak'},.012)
    for x in (-.47,-.36,-.29,.12,.38,.45):
        for z in (.611,.904,1.14,2.045,2.347):
            if (x,z) in ((.12,2.045),(.38,.611)):
                from_front('Ten-millimetre rebate between diagonal boards',x,z,{'rebated seam'},.002)
            else:
                from_front('Independent chamfered timber boards',x,z,{'painted teak','alternate teak'},.012)
    for sign in (-1,1):
        for z in (.39,.765,1.71,2.23):
            from_front('Outer casing',sign*.579,z,{'timber frame'},.024)
            from_front('Central casing',sign*.564,z,{'timber frame'},.038)
            from_front('Inner projecting casing',sign*.52,z,{'timber frame'},.052)
            from_front('Cream rear plane',sign*.70,max(z,.80),{'cream plaster'},-.025)
    for x in (-.73,-.30,.00,.37,.71):cast('Granite threshold',(x,-.28,.42),(0,0,-1),.7,{'stone sill'},.42-.176)
    for x in (-.08,.02,.076):
        for z in (-.02,.03):cast('Timber fully removed in the glazed aperture',(x,.060,1.703+z),(0,-1,0),.049)
    for px,py in [(244,277),(239,348),(270,339),(244,375),(227,406),(257,441)]:
        x=-.008+(px-249)*.232/125;z=1.703+(359-py)*.232/130
        cast('Back of glass in a real opening',(x,.05,z),(0,-1,0),.15,{'textured glass'},.05-.008)
    for px,py in [(252.62,425.24),(253.70,385.97),(199.32,331.06),(279.62,339.72),(185.98,351.79),(309.94,353.22),(263.00,289.16),(215.66,286.40),(263.70,295.00),(247.65,285.84)]:
        x=-.008+(px-249)*.232/125;z=1.703+(359-py)*.232/130
        from_front('Individual iron curve or lattice rail',x,z,{'hammered iron'},.031)
    for x,z in ((.147,2.18),(.266,2.156),(.152,2.146),(.222,2.185)):
        from_front('Dark plate bearing the number six',x,z,{'dark patinated brass'},.023)
    for side in (-1,1):
        for z in (.75,1.05,1.45,1.80,2.35):cast('Clear standing space inside the recess',(side*.32,-.46,z),(0,1,0),.40)
    return dict(passed=all(v['passed'] for v in rows),samples=rows)

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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
