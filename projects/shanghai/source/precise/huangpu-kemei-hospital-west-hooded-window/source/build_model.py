"""Build the surveyed hooded brick window bay on the former Kemei Hospital."""
from pathlib import Path
import sys
import os
from argparse import ArgumentParser
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from west_window import PALETTE, add_building
ID='huangpu-kemei-hospital-west-hooded-window'
NAME='克美产科医院旧址西墙挑檐窗'
SCOPE='重庆南路139号，市表4C008所列2号楼朝西的上层挑檐窗、可见栏墙压顶及一窗宽红砖檐带。'
META={
    'id':ID,'name':NAME,'viewer_page':'kemei-hospital-west-hooded-window.html',
    'status':'photo-informed-kemei-hospital-west-hooded-window','model_scope_zh':SCOPE,'scope':SCOPE,
    'estimated':'2020年2月及2021年1月街照可辨挑檐、窗洞和砖带。两座2021实景站提供尺寸；视线交会的高程差最高约0.85米。挑檐厚度和玻璃暗部依据照片估计。',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'coordinate_convention':'Metres, Z up. Local X follows the west facade south. Positive Y runs inward. The upper wall fragment begins approximately 7.32m above ground.',
    'copyright':'Original geometry under MIT. Documentary images are credited and not embedded.'
}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['KEMEI_334_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
