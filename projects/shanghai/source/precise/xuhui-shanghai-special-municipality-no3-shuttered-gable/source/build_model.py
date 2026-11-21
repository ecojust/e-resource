"""Build the shuttered attic gable of building 3 at 48 Pingjiang Road."""
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
from municipal_gable import PALETTE,add_building,texture
ID='xuhui-shanghai-special-municipality-no3-shuttered-gable'
SCOPE='平江路48号3号楼中央阁楼的红砖山墙、四扇百叶、窗楣和两道斜封檐。'
META=dict(id=ID,name='上海特别市市政府旧址3号楼砖山墙与四扇百叶',viewer_page='special-municipality-no3-shuttered-gable.html',
    scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=4.89,estimated='山墙正面按原照比例制作，整体尺度和两侧截断深度为估算。',
    source_register='source/precise/'+ID+'/reference-review.json',copyright='Original geometry, rendered brick pattern and procedural wear.')
if __name__=='__main__':
    texture(source/'running-bond.png')
    build(source,META,PALETTE,add_building)
