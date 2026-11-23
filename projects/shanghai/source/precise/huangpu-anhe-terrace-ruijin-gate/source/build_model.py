"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gate import PALETTE,add_gate
ID='huangpu-anhe-terrace-ruijin-gate'
SCOPE='瑞金二路198弄朝街入口的两座水刷石门墩、南墩两面可读门牌与布告牌、2021年闭合的平顶双扇金饰铁门和南扇小门。'
META=dict(id=ID,name='安和新村瑞金二路198弄金饰铁门与门牌柱',viewer_page='anhe-terrace-ruijin-gate.html',scope=SCOPE,model_scope_zh=SCOPE,source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,status='photo-informed-surveyed-lane-entrance',estimated='五幅原球面街照配准。门洞净宽4.09±0.35米，墩顶约4.03±0.35米；正面与门背断面、卷枝样式为实照基础上的简化。',coordinate_convention='Metres. X follows the street to the north-northwest. Y points into the lane. Z is height above the entrance threshold.',copyright='Original geometric reconstruction. Plaque lettering uses Noto Sans CJK, SIL OFL 1.1. Documentary photographs are credited separately.')
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['ANHE_GATE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_gate)
