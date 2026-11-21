"""Package the documented western roof of the southern Fenyang Road twin."""
from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if 'SHANGHAI_MODEL_TOOLS' in os.environ:roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
project=next(root for root in roots if (root/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(project/'tools'))
from package_architectural_model import build
from west_roof_bay import PALETTE,add_building,EAVE

ID='xuhui-fenyang-twin-villa-west-roof-bay'
SCOPE='南栋西端上部的两段坡瓦、前檐横向阁窗、挑檐木托及下一排成对开窗。'
META=dict(id=ID,name='汾阳路152–154号并立花园住宅西端折坡瓦檐与阁窗',
 viewer_page='fenyang-twin-villa-west-roof-bay.html',status='photo-informed-exterior-study',
 scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=EAVE+5.85,
 estimated='端部墙宽约8.16米，两幢同形足印与2020年照片共同约束檐宽和横窗位置。屋面绝对高度、切回深度及瓦片细分为估计。',
 source_register='source/precise/'+ID+'/reference-review.json',coordinate_convention='Metres. Origin at the southwest bay centreline on the south wall at ground level. +X east, +Y inward, +Z up.',
 interiors_modeled=False,copyright='Original mesh and finishes based on visual research. The 2020 survey was photographed by Legolas1024 (CC BY-SA 3.0). No source photograph forms part of the model surface.')
if __name__=='__main__':build(source,META,PALETTE,add_building)
