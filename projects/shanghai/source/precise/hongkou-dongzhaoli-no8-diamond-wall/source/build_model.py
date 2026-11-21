"""Build the photographed gate pier and adjoining lozenge relief at Dongzhaoli."""
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
from dongzhao_wall import PALETTE,add_building,texture
ID='hongkou-dongzhaoli-no8-diamond-wall'
META=dict(id=ID,name='东照里八号门柱与菱形院墙',viewer_page='dongzhaoli-diamond-wall.html',
    model_scope_zh='2015年山阴路133弄原照中的绿色8号牌、分缝石门柱与相连的一格菱形院墙。',
    reference_height_m=2.408,estimated='比例依据现场照片，绝对尺寸、背面和石料深度据可见部位估算。',
    source_register='source/precise/'+ID+'/reference-review.json',copyright='Original model, numeral outline and mineral-grain texture.')
META['scope']=META['model_scope_zh']
if __name__=='__main__':
    texture(source/'mineral-grain.png')
    build(source,META,PALETTE,add_building)
