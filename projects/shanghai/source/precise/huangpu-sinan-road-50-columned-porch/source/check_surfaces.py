"""Reopen both packed levels and cast against the measured column, paving, doorway, number plaque and hipped-roof planes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-sinan-road-50-columned-porch'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows = []

    def ray(title, origin, direction, length, materials=(), expected=None, tolerance=.015):
        hit = scene.ray(list(origin), list(direction), length)
        if materials:
            passed = (hit is not None and hit['material'] in materials
                      and abs(hit['distance_m'] - expected) <= tolerance)
        else:
            passed = hit is None
        rows.append(dict(check=title, origin=origin, direction=direction, max_length=length,
                         allowed_materials=list(materials), expected_distance_m=expected,
                         tolerance_m=tolerance, hit=hit, passed=passed))

    streetward_start = -1.7
    for x in (-.62,-.27,.06,.39):
        for y,z in ((-1.34,.16),(-1.13,.31),(-.87,.455),(-.45,.59)):
            ray('Four separate stone tread heights', (x,y,1), (0,0,-1), 1,
                ('granite facing','step edge'),1-z)
    for z,r in ((.5,.255),(.718,.229),(.82,.18),(.95,.164),(1.5,.159),(2.3,.152),
                (2.9,.146),(3.052,.202),(3.12,.226)):
        material='granite facing' if z<.69 else 'painted stucco'
        ray('Surveyed base, single tapered column and capital',(.765,streetward_start,z),
            (0,1,0),1,(material,),-1.09-r-streetward_start,.023)
    for x in (-.81,-.51,-.12,.21,.50):
        for z in (1.04,1.49,2.18,2.69,2.97):
            ray('Open porch floor between return and single column',(x,-1.45,z),(0,1,0),.99)
        ray('Exposed underside of projecting entrance beam',(x,-1.11,2.15),(0,0,1),
            1.2,('painted stucco',),3.127-2.15)
    for z in (.27,.62,1.51,2.44,2.87):
        name,depth=('granite facing',-1.184)if z<.53 else ('painted stucco',-1.18)if 1.47<z<1.525 else ('pebble dash',-1.16)
        ray('Opposite beam end has a wall return',(-1.2,-1.45,z),(0,1,0),1,
            (name,),depth+1.45)
    for x in (-.425,-.155):
        ray('Two separate vertical glazing bars',(x,-.53,2.53),(0,1,0),.6,
            ('aged timber',),.53-.151)
    for x in (-.52,-.27,.05):
        ray('Recessed door glazing behind the porch',(x,-.53,2.53),(0,1,0),.6,
            ('glazing',),.53-.131)
        ray('Separate rail crossing the glazed light',(x,-.53,2.258),(0,1,0),.6,
            ('aged timber',),.53-.153)
    for x,z in ((.411,2.355),(.535,2.448),(.682,2.514),(.647,2.368)):
        ray('Brass street number plaque',(x,-.41,z),(0,1,0),.5,
            ('address brass',),.41-.203)
    for x,z in ((.466,2.535),(.446,2.510),(.484,2.431),(.615,2.484),(.587,2.539),(.559,2.484)):
        ray('Raised figures on the 50 address plaque',(x,-.41,z),(0,1,0),.5,
            ('dark enamel',),.41-.211)
    for x in (-.94,-.71,-.49,-.17,.11,.34,.59,.95):
        for y in (-1.41,-1.23,-1.07,-.92):
            k=(y+1.53)/.84
            # The short ridge ends slope onto the east and west hips.
            if x < -1.87+(1.47*k)+.035 or x > 1.65-(1.27*k)-.035:continue
            surface_z=3.96+(.83*k)
            ray('Hipped tile plane above the porch',(x,y,5.2),(0,0,-1),2,
                ('reddish tile','sunlit tile','dark tile overlap'),5.2-surface_z,.052)
    for x in (-.30,-.15,0,.14,.29):
        ray('Short raised ridge',(x,-.69,5.25),(0,0,-1),1,
            ('reddish tile',),5.25-(4.79+.044+.046),.012)
    for x in (-2.06,1.84):
        for z in (.15,1.6,2.8,3.48,4.32):
            ray('No geometry on adjacent facades',(x,-1.7,z),(0,1,0),2.5)
    return dict(passed=all(a['passed'] for a in rows),samples=rows)

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
