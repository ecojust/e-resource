"""Build Residence A's broad garden loggia and east return."""
import argparse
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from ailu_loggia import PALETTE,add_ailu
ID='xuhui-ailu-residence-garden-loggia'
SCOPE='东平路9号音乐学院附校甲楼园侧大小两座两层敞廊、宽券和侧券、石栏与凸出阳台、廊内门窗、西侧老虎窗和东翼可见的一段坡屋面。'
META=dict(id=ID,name='东平路9号爱庐甲楼花园敞廊',viewer_page='ailu-residence.html',scope=SCOPE,model_scope_zh=SCOPE,
    status='garden elevation documented in a photograph published in 2015',
    source_register='source/precise/'+ID+'/reference-review.json',
    estimated='庭面南向、临庭边长23.49米由地块及航片复核。券高、栏杆、廊进深、屋顶及烟囱按照片比例估计。后部及乙楼保留。',
    interiors_modeled=False,coordinate_convention='X east along the garden wall, Y north into house, Z up. glTF +Z toward garden.',
    copyright='Original model and code under MIT. Reference photos and map data are credited separately.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['AILU_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_ailu)
    audit_path=Path(remaining[remaining.index('--audit')+1])/'geometry-native.json'
    report=json.loads(audit_path.read_bytes())
    report['render']='Cycles, 12 samples, from reopened blend. OIDN RT sRGB postfilter.'
    audit_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
