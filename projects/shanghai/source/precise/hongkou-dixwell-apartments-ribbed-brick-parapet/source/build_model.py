"""Build the upper street facade and ribbed brick parapet on the Dixwell Apartments."""
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
from parapet import PALETTE, add_building, texture
ID='hongkou-dixwell-apartments-ribbed-brick-parapet'
META=dict(id=ID,name='狄思威公寓四川北路砖砌女儿墙冠与窗檐',viewer_page='dixwell-brick-parapet.html',
    model_scope_zh='临街上缘一组深红砖砌女儿墙冠、五道凸脊、浅色压沿及其下同组两扇钢窗和板檐。',
    reference_height_m=4.3,estimated='按两期原照比对建模，出挑深度、钢件截面及绝对尺度为展示估值。',
    source_register='source/precise/'+ID+'/reference-review.json',copyright='Original mesh and procedural facing brick.')
META['scope']=META['model_scope_zh']
if __name__=='__main__':
    texture(source/'brick-courses.png')
    build(source,META,PALETTE,add_building)
