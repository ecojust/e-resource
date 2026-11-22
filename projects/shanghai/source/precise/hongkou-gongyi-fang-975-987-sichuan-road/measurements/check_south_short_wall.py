"""Check first visible material and depth from the south for the seven documented openings."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene


def measure(mesh):
    scene = SerialScene(mesh)
    observations = json.loads((HERE / 'south-short-wall-window-observations.json').read_bytes())
    records = []
    def hit(label, s, z, suffix, depth):
        result = scene.ray((-1.0, s, z), (1, 0, 0), 1.5)
        assert result is not None, (label, s, z)
        x = result['point_enu_m'][0]
        ok = result['material'] == 'Gongyi 3 | ' + suffix and abs(x-depth) < .008
        records.append(dict(label=label, s_m=s, z_m=z, expected_depth_m=depth, expected=suffix, first_hit=result, passed=ok))

    for opening in observations['openings']:
        name = opening['id']
        s = opening['s']
        a = opening['width'] / 2
        mid = opening['top_z'] - opening['height'] / 2
        top = opening['top_z']
        bottom = top - opening['height']
        hit(name+' centre', s, mid, 'shaded end-wall inset', .215)
        hit(name+' near side of inset', s-a+.10, mid, 'shaded end-wall inset', .215)
        hit(name+' inner jamb', s+a-.022, mid, 'pale stone dressings', .135)
        hit(name+' outer jamb', s-a-.032, mid, 'pale stone dressings', -.049)
        brick_s = s-a-.145 if name=='South L3 west' else s+a+.145
        hit(name+' exterior brick', brick_s, mid, 'cleaned running-bond brick', 0.)
        hit(name+' lintel', s, top+.098, 'pale stone dressings', -.12)
        hit(name+' sill', s, bottom-.041, 'grey-beige washed aggregate', -.085)
    for label,s,z in [('east lower dressing',4.65,6.0),('west lower dressing',9.6,6.1),('between openings',7.92,10.6)]:
        suffix,depth=('cleaned running-bond brick',0.) if label=='between openings' else ('pale stone dressings',-.037)
        hit(label,s,z,suffix,depth)
    passed = sum(x['passed'] for x in records)
    return dict(asset=scene.asset,coordinates='X into south wall, s towards rear, Z upwards, metres',passed=passed==len(records),count=len(records),matches=passed,checks=records)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    report=measure(args.mesh)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(report['matches'],report['count'],report['asset']['sha256'])
    if not report['passed']:
        for rec in report['checks']:
            if not rec['passed']:
                print(rec['label'],rec['first_hit'])
        raise SystemExit(1)
