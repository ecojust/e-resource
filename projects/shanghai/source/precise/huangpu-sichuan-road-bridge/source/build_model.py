"""Build the Sichuan Road Bridge river elevations, roadway and both sidewalks."""
import argparse
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from sichuan_bridge import PALETTE,build_bridge
ID='huangpu-sichuan-road-bridge'
SCOPE='跨越苏州河的四川路桥三孔可见桥身、两侧实心栏墙、四座灯柱、车行道和两条人行道；桥西北邮政总局、乍浦路桥与两岸原有楼房保留。'
META=dict(id=ID,name='四川路桥三孔桥身与两侧人行道',viewer_page='sichuan-road-bridge.html',scope=SCOPE,model_scope_zh=SCOPE,
    status='exterior documented in 2010 and 2014; archival listed dimensions',
    source_register='source/precise/'+ID+'/reference-review.json',
    estimated='市政志给出70.97米全长、三跨径和12.8米车道、两侧各2.7米步道。灯座高度、可见梁腹弧线、板缝与桥面起伏依据两期实照估算。',
    interiors_modeled=False,coordinate_convention='X along the bridge towards north (353.348 degrees), Y west across the deck (263.348 degrees), Z up from an estimated photographic waterline.',
    copyright='Original model and source under MIT. Photographs are separately credited, measurements use cited sources.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['SICHUAN_BRIDGE_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,build_bridge)
    manifest_path=Path(remaining[remaining.index('--out')+1])/'manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    manifest['all_dimensions_estimated']=False
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    audit_path=Path(remaining[remaining.index('--audit')+1])/'geometry-native.json'
    report=json.loads(audit_path.read_bytes())
    report['render']='Cycles, 12 samples, from reopened blend. OIDN RT sRGB postfilter.'
    audit_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
