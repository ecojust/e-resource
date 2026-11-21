"""Package the former Jiangnan general office in the Shanghai Expo area."""
from pathlib import Path
import argparse
import os
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from general_office import PALETTE, add_general_office

IDENT='huangpu-jiangnan-historic-general-office'
SCOPE='江南制造局旧址总办公楼（西公务厅）的南向两层正立面、两座门廊与凹字形三翼红瓦屋顶。临街窗列按多期实照制作，院内回翼按屋顶和墙体轮廓简化。'
META=dict(id=IDENT,name='江南制造局旧址总办公楼（西公务厅）',status='original-photo-informed-historic-exterior',
          viewer_page='jiangnan-historic-general-office.html',scope=SCOPE,model_scope_zh=SCOPE,
          interiors_modeled=False,source_register=f'source/precise/{IDENT}/reference-review.json',
          estimated='按2013、2015、2021年龙华东路照片和两期航片估算门窗、檐线、屋脊及门廊尺寸。',
          coordinate_convention='Local +X east along the south elevation, +Y towards the courtyard, +Z up.',
          copyright='Original MIT model; reference photographs and imagery cited by URL.')
if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['JIANGNAN_OFFICE_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_general_office)
