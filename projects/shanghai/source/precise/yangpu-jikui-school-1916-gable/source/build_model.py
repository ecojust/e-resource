import os
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
roots = list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0, Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools = next(parent/'tools' for parent in roots if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(tools))
from package_architectural_model import build
from school_gable import ID, PALETTE, add_building, texture

scope='荆州路42号教学楼的2014年照片可见两个带纪年的山墙。这里取左边较近的一端，制作坡檐、嵌于屋脊下方的小百叶通风口、四位纪年及三扇窗的楣部。'
META=dict(id=ID,name='缉槼中学教学楼山墙1916纪年与百叶通风口',scope=scope,model_scope_zh=scope,viewer_page='jikui-school-1916-gable.html',reference_height_m=2.72,all_dimensions_estimated=True,estimated='1916按图中的铭文刻画。窗体下部、围墙及另一端山墙不在取样内；字形和砌体深度依据正面像素近似。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
