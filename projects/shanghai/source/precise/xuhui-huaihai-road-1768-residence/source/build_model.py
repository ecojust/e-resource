"""Build the documented house beside the south gate of Lane 1768."""
import argparse
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from lane_residence import PALETTE,add_residence
ID='xuhui-huaihai-road-1768-residence'
SCOPE='原淮海中路1754弄、今1768弄南门东侧三层住宅的沿街双拱形底窗、二层四扇直棂窗、上层四扇弧顶窗、窗前护栏、檐带、实拍侧窗及1768弄绿牌。以两期航片约束院侧轮廓和坡屋顶。'
META=dict(id=ID,name='霞飞别墅淮海中路1768弄口临街住宅',viewer_page='huaihai-road-1768-residence.html',scope=SCOPE,model_scope_zh=SCOPE,
    status='Gate-side exterior observed in photographs published in 2013 and captured in January 2015.',
    source_register='source/precise/'+ID+'/reference-review.json',
    estimated='街面宽9.489米及四角取冻结轮廓。层高、栏杆、屋脊、细枝和色彩按实照估计；未见侧后窗、园内诸栋和街边电话亭未建。',
    interiors_modeled=False,coordinate_convention='X northeast along the street, Y northwest into house, Z up. glTF +Z faces Huaihai Middle Road.',
    copyright='Original mesh and code MIT. Sources and OFL typeface credited separately.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['LANE_RESIDENCE_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_residence)
    audit_path=Path(remaining[remaining.index('--audit')+1])/'geometry-native.json'
    report=json.loads(audit_path.read_bytes())
    report['render']='Cycles, 12 samples, from reopened blend. OIDN RT sRGB postfilter.'
    audit_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
