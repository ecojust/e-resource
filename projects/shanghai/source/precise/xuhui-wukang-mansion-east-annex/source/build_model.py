"""Package the front of the 1930 east annex of Wukang Mansion."""
from pathlib import Path
import argparse
import os
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from annex import PALETTE,build_annex
ID='xuhui-wukang-mansion-east-annex'
SCOPE='1930年武康大楼东侧副楼的淮海中路临街面。两层红砖基座、1834号书店门窗、上三排横窗及两端弧转、外露罩与端墙按2020年街景和2024年门面近照制作。'
META=dict(id=ID,name='武康大楼东侧副楼临淮海中路立面',viewer_page='wukang-east-annex.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='photographed-five-storey-street-elevation',source_register='source/precise/'+ID+'/reference-review.json',
          estimated='五层有文献记录，临街宽度按冻结320和开放地图配准。窗带及红砖基座尺寸按多机位照片估算。保留原武康大楼主楼、背街部分及435号原汽车间。',interiors_modeled=False,
          coordinate_convention='Author X north-east along Huaihai Middle Road; Y north-west into the building; Z up. glTF +Z faces the street.',
          copyright='Original geometric study under MIT; subset typeface under SIL OFL 1.1. Reference photographs linked separately.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['WUKANG_EAST_ANNEX_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,build_annex)
