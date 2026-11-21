"""Build the documented section of the garden terrace at 205 Kangping Road."""
import os
from pathlib import Path
import sys

source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from terrace import PALETTE,add_building,finish
ID='xuhui-kangping-205-garden-terrace-balustrade'
SCOPE='据徐汇区绿化和市容管理局归档的二层露台正斜两照，制作一个方形转角墩、一段双向瓶栏、扶手与阶形檐托。'
META=dict(id=ID,name='康平路205号花园住宅露台瓶栏与檐托',viewer_page='kangping-205-terrace-balustrade.html',
    scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=1.307,estimated='高度、栏杆间距、转角进深按照片估算，表现局部比例。',
    source_register='source/precise/'+ID+'/reference-review.json',copyright='Original mesh and procedural mineral finish.')
if __name__=='__main__':
    finish(source/'mineral-finish.png')
    build(source,META,PALETTE,add_building)
