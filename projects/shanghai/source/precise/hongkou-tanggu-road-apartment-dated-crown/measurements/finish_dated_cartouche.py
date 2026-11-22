"""Check the source mesh and its two decoded LODs, then render the dated crown study plate."""
import argparse
import json
from pathlib import Path
from check_dated_cartouche import check
from render_dated_cartouche import make_board
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('packaged',type=Path,help='Directory with raw.glb, decoded-full.glb, decoded-lod.glb')
parser.add_argument('audit',type=Path,help='Dated cartouche output directory')
parser.add_argument('--layout',type=Path,default=HERE/'cartouche-layout.json')
args=parser.parse_args()
layout=json.loads(args.layout.read_bytes())
args.audit.mkdir(parents=True,exist_ok=True)
for role,name in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
    report=check(args.packaged/name,layout)
    (args.audit/f'whole-{role}.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
    print(role,report['checks'],report['passed'],flush=True)
    if not report['passed']:
        for item in report['rows']:
            if not item['passed']: print(item,flush=True)
        raise SystemExit(1)
make_board(args.packaged/'decoded-full.glb',args.audit/'dated-cartouche.jpg',layout)
