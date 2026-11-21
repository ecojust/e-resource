"""Build the field-facing upper balcony of the former school at 102 Zhongzhou Road."""
import os
import sys
from pathlib import Path
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from courtyard_balcony import PALETTE, add_building, texture
ID='hongkou-zhongzhou-school-central-balcony'
META=dict(id=ID,name='华童公学中州路校舍操场侧中央阳台与钢窗',viewer_page='zhongzhou-school-central-balcony.html',
    model_scope_zh='操场侧长教学楼三层中央阳台、双扇门、左右各两扇钢窗及上覆灰瓦檐。',
    reference_height_m=4.4,estimated='照片投影比例有据，墙深、栏杆出挑、玻璃颜色与瓦面细缝均近似。',
    source_register='source/precise/'+ID+'/reference-review.json',copyright='Original mesh and tile texture.')
META['scope']=META['model_scope_zh']
if __name__=='__main__':
    texture(source/'gray-tiles.png')
    build(source,META,PALETTE,add_building)
