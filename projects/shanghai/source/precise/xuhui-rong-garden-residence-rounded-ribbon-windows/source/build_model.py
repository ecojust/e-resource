"""Build the garden-facing ribbon windows of the residence at 20 Lane 18 Gao'an Road."""
from pathlib import Path
import os
import sys

source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from ribbon_windows import add_building, make_texture, PALETTE

ID='xuhui-rong-garden-residence-rounded-ribbon-windows'
SCOPE='依据2015年10月花园正照，制作左翼两层圆端带窗、转角钢窗及出挑遮阳板。'
META=dict(id=ID,name='荣氏花园住宅园面双层圆端带窗',viewer_page='rong-garden-rounded-ribbon-windows.html',
          scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=5.51,estimated='窗高、层间距及窗框深度按照片比例估算。',
          source_register='source/precise/'+ID+'/reference-review.json',
          copyright='Original mesh and procedural stucco. The cited historical photographs are not embedded.')
if __name__=='__main__':
    make_texture(source/'roughcast.png')
    build(source,META,PALETTE,add_building)
