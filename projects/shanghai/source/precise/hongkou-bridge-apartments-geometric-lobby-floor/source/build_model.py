"""Build the geometric entrance lobby inlay at 85 North Sichuan Road."""
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
from lobby_inlay import PALETTE,add_building,texture
ID='hongkou-bridge-apartments-geometric-lobby-floor'
SCOPE='四川北路85号大桥公寓门厅中央方形拼花及其外围窄幅地面。'
META=dict(id=ID,name='大桥公寓门厅方形几何拼花地面',viewer_page='bridge-apartments-lobby-floor.html',
    scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=.066,estimated='地面图案按2013年门厅实照校正透视，展示边长与剖边厚度为估算。',
    source_register='source/precise/'+ID+'/reference-review.json',copyright='Original geometry, mineral inlay and procedural aggregate.')
if __name__=='__main__':
    texture(source/'original-aggregate.png')
    build(source,META,PALETTE,add_building)
