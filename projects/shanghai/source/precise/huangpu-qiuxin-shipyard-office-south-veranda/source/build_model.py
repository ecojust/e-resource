"""Package the photo-based south iron porch of the former Qiuxin Shipyard office."""
from pathlib import Path
import argparse
import os
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from veranda import PALETTE,add_veranda
ID='huangpu-qiuxin-shipyard-office-south-veranda'
SCOPE='求新船厂1923年厂部办公楼南立面的两层铸铁外廊、成对铁柱、植物纹挂落、红色窗框与砖墙。双坡屋面及两烟囱按修复实景简化，背面仅留体量。'
META=dict(id=ID,name='求新船厂厂部办公楼南立面铸铁外廊',viewer_page='qiuxin-shipyard-office-south-veranda.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-historic-exterior',source_register=f'source/precise/{ID}/reference-review.json',estimated='面宽由源地边界量取。檐口由三个公共摄影点估计，柱径、铸花、屋顶高度与被枝叶遮住的开间按实照比例取近似值。',coordinate_convention='Metres, +X eastward along the south facade, +Y inland into the office, +Z up.',interiors_modeled=False,copyright='Original MIT mesh and materials. External photographs remain separately credited.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['QIUXIN_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_veranda)
