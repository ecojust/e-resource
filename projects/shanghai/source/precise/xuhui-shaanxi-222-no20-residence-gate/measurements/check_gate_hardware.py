"""Compare native photo pixels with first surfaces of the two knockers, house number and call plate."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys

from register_gate import Camera

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from gate_hardware import CAST, RIDGE, HOLLOW, ENAMEL, PAINT, ALLOY, GREY, RED

HEAD = (CAST, HOLLOW, RIDGE)
LEAF = 'black door seen through the ring'
SAMPLES = {
    '06': [
        ('left medallion top',(248,779),HEAD),('left low forehead',(245,785),HEAD),
        ('left nose',(247,795),HEAD),('left cheek',(234,793),HEAD),
        ('left open ring',(248,817),(LEAF,)),('left worn hoop bottom',(248,824),(RIDGE,)),
        ('right medallion top',(328,779),HEAD),('right low forehead',(325,785),HEAD),
        ('right nose',(327,795),HEAD),('right cheek',(313,793),HEAD),
        ('right open ring',(328,817),(LEAF,)),('right worn hoop bottom',(327,824),(RIDGE,)),
        ('plate upper left',(266,443),(ENAMEL,)),('open centre of zero',(301,452),(ENAMEL,)),
        ('two top',(284,446),(PAINT,)),('two baseline',(286,462),(PAINT,)),
        ('zero left stroke',(296,454),(PAINT,)),('zero right stroke',(304,454),(PAINT,)),
        ('bell border',(517,799),(ALLOY,)),('bell label window',(531,800),(ALLOY,GREY)),
        ('bell dark insert',(527,817),(HOLLOW,)),('bell red point',(540,825),(RED,))],
    '07': [
        ('plate upper left',(300,305),(ENAMEL,)),('teal below numerals',(321,321),(ENAMEL,)),
        ('two baseline',(313,318),(PAINT,)),('zero right stroke',(325,313),(PAINT,)),
        ('green at lower right',(335,328),(ENAMEL,))]
}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    project=HERE.parents[3]
    scene=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](args.mesh)
    rows=[]
    for view,samples in SAMPLES.items():
        camera=Camera(view)
        for feature,pixel,expected in samples:
            hit=scene.ray(camera.c,camera.ray(pixel),20)
            material=hit['material'] if hit else None
            if LEAF in expected:
                # On the standalone hardware mesh the opening is clear through.
                # On the assembled building the ray reaches the dark door leaf.
                passed=not hit or material=='Shaanxi 222-20 | charcoal double door'
            else:
                passed=material in expected
            rows.append(dict(view=view,feature=feature,pixel=pixel,expected=expected,first_hit=hit,passed=passed))
    report=dict(mesh=args.mesh.name,sha256=sha256(args.mesh.read_bytes()).hexdigest(),
                cameras_sha256=sha256((HERE/'portal-cameras.json').read_bytes()).hexdigest(),
                units='metres; integer native photo pixels, images 690×1038 and 690×459',
                counts={v:[sum(r['passed'] for r in rows if r['view']==v),len(SAMPLES[v])]for v in SAMPLES},
                passed=sum(r['passed'] for r in rows),total=len(rows),samples=rows)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(report['passed'],len(rows),[(r['view'],r['feature'],(r['first_hit'] or {}).get('material'))for r in rows if not r['passed']])
if __name__=='__main__':main()
