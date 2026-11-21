"""Build the Ampire Building elevation on Yuanmingyuan Road."""
import argparse
import json
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from ampire import PALETTE,add_ampire
ID='huangpu-ampire-and-co-building'
SCOPE='圆明园路97号东立面四层窗、红砖拱门及券石、两侧三开间、中央圆形挑窗、双弧形窗冠、双三角山花、两块AMPIRE铭带和两端圆弧翼。仅取临街浅进深。'
META=dict(id=ID,name='安培洋行大楼圆明园路主立面',viewer_page='ampire-and-co.html',scope=SCOPE,model_scope_zh=SCOPE,
    source_register='source/precise/'+ID+'/reference-review.json',
    status='East street elevation observed in 2014 and subsequently published street views.',
    estimated='平面可见宽约32米，建筑高度、窗棂、砖缝、两翼弧度和截深依据照片估计。登记次级表记三层，正面实照可见四排楼层窗。',interiors_modeled=False,
    coordinate_convention='X along the street to the north, Y west into the building, Z up. glTF +Z looks toward the street.',
    copyright='Original mesh and code MIT. No source photography redistributed as textures.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['AMPIRE_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_ampire)
    audit_path=Path(remaining[remaining.index('--audit')+1])/'geometry-native.json'
    report=json.loads(audit_path.read_bytes())
    report['render']='Cycles, 12 samples, from reopened blend. OIDN RT sRGB postfilter.'
    audit_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
