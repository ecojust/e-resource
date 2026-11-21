from pathlib import Path
import os,sys
source=Path(__file__).resolve().parent
roots=list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):roots.insert(0,Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools=next(p/'tools' for p in roots if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(tools))
from package_architectural_model import build
from arched_gable import PALETTE,add_building,texture
ID='yangpu-tung-hing-mill-no51-twin-arched-gable'
scope='平凉路1777弄51号住宅照片中同一处坡顶山墙、两扇独立拱窗及下方三面折窗。尺寸按照片比例估算。'
META=dict(id=ID,name='同兴纱厂51号住宅折坡山墙与双拱窗',scope=scope,model_scope_zh=scope,viewer_page='tung-hing-no51-twin-arched-gable.html',reference_height_m=5.15,estimated='外形和构件依公开近照，绝对尺度与墙厚估算。',copyright='Original mesh and original procedural ochre render.')
if __name__=='__main__':
    texture(source/'ochre-render.png')
    build(source,META,PALETTE,add_building)

