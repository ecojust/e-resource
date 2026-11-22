"""Model the canted window tower on the Beijing Road street side of the Zhu side porch."""
import argparse
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from porch import PALETTE,add_geometry
ID='jingan-zhu-douwen-residence-side-porch'
SCOPE='康定路759号朱斗文公馆侧门方柱、卷托、半圆门套、曲面木格凸窗、露台瓶栏与外墙圆花饰。'
META=dict(id=ID,name='朱斗文公馆侧门柱廊与弧窗',viewer_page='zhu-douwen-side-porch.html',
 scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed east side entrance and bow window',source_register=f'source/precise/{ID}/reference-review.json',
 estimated='平台位置参照带突出部的足印和两期屋顶影像。木格窗曲率、檐口和门廊高度、卷托剖面与花瓣后部均按署名照片估计。',
 interiors_modeled=False,coordinate_convention='Metres, Z up. Positive X follows the eastern side wall toward north, positive Y points into the house.',
 copyright='Original geometry and procedural wall finish under MIT. Research photographs retain their individual rights.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--audit',type=Path,required=True)
    options,remaining=parser.parse_known_args()
    os.environ['ZHU_PORCH_BLENDER']=options.blender
    sys.argv[1:]=[*remaining,'--audit',str(options.audit),'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
    import json
    record=options.audit/'geometry-native.json'
    proof=json.loads(record.read_bytes())
    assert proof['native_reopened_and_compared']['porch_reopened']['active_camera']=='Zhu side porch Porch and bow'
    proof['render']='Cycles, 14 samples, from reopened blend. OIDN RT sRGB postfilter.'
    record.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
