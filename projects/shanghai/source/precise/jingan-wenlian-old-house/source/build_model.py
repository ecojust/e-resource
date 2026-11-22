"""Build the existing south garden elevation at 238 Yan'an West Road."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from garden_front import PALETTE,make_garden_front
ID='jingan-wenlian-old-house'
SCOPE='延安西路238号市文联老楼南园面，两层敞廊、成对廊柱、石栏杆、两翼切角凸窗、曲顶山花和六轴上层窗。'
META=dict(id=ID,name='文联老楼南园面',status='original-photo-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,viewer_page='wenlian-old-house.html',estimated='20世纪20年代中期建造，房产证记1925年。南园面尺度、材色及檐深依据1995年和修缮完成后的照片与市图估计。东侧另址的1941年意大利总会大礼堂见历史待制说明。',coordinate_convention='X runs east along the garden elevation. Y points into the house. glTF +Y is up.',source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,copyright='Original MIT geometry. Photographs are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_garden_front)
