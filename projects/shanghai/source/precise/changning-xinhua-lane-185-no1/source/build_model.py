"""Package the restored south garden elevation, portico and roof."""
from pathlib import Path
import argparse
import os
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from house import PALETTE,build_residence
ID='changning-xinhua-lane-185-no1'
SCOPE='新华路185弄1号修后花园南立面。三开间券廊可穿行，九块镂空露台栏板、红砖山墙、重置仿钢窗、棚式老虎窗、红瓦主脊与三座烟囱按四普和实景俯照制作。'
META=dict(id=ID,name='新华路185弄1号花园住宅',viewer_page='xinhua-lane-185-no1.html',scope=SCOPE,model_scope_zh=SCOPE,status='restored-garden-elevation-and-roof',estimated='据修缮后实照、四普照片、两期航片和门牌点估算，隐藏的侧后面采取简化轮廓。',coordinate_convention='Local X follows the garden frontage towards the east-southeast, local Y points into the house towards the north-northeast, and Z is up. glTF +Z faces the garden.',model_period='第四次全国文物普查及2026年刊出的修缮后外观，第三次普查旧状另记。',source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,copyright='Original geometry MIT. No reference photographs are embedded.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['XINHUA_LANE_185_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,build_residence)
