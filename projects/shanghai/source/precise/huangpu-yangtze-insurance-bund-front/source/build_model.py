"""Package the photographed Bund front at 26 East Zhongshan No. 1 Road."""
from pathlib import Path
import argparse
import os
import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from yangtze_facade import PALETTE, add_yangtze
IDENT='huangpu-yangtze-insurance-bund-front'
SCOPE='扬子水火保险公司外滩26号临江东立面。重建五轴街墙、下部券窗及两侧门、六层中央双柱廊、顶层两侧窗亭和退台。'
META=dict(id=IDENT,name='扬子大楼外滩26号临江东立面',status='original-photo-informed-historic-exterior',
          viewer_page='yangtze-insurance-bund-front.html',scope=SCOPE,model_scope_zh=SCOPE,
          interiors_modeled=False,source_register=f'source/precise/{IDENT}/reference-review.json',
          estimated='东侧面宽按照原建筑源面量取；檐口高度、窗洞、柱廊和退台按实照比例估算。',
          coordinate_convention='Local +X runs north along the Bund facade, +Y west into the study, +Z upward.',
          copyright='Original MIT geometry. Photographs are cited separately. Subset typeface under SIL OFL 1.1.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['YANGTZE_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_yangtze)
