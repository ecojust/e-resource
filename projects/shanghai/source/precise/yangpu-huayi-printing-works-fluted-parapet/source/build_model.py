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
from printing_works import ID, PALETTE, add_building, texture

scope='2015年榆林路308号临街照片中，上层钢窗以上的灰色女儿墙布满竖向凸槽，窗下为灰色窄肋分开的红砖填面。这里取原照中上排相邻两扇窗及其上、下收边。'
META=dict(id=ID,name='华一印刷股份有限公司旧址竖槽女儿墙与砖填窗间',scope=scope,model_scope_zh=scope,viewer_page='huayi-printing-works-fluted-parapet.html',reference_height_m=2.93,all_dimensions_estimated=True,estimated='资料将历史名称写作华生印务公司及华一印刷股份有限公司。取景可核到临街一面，截段宽高和凸槽进深为照片比例估算，空调机、店牌和线路不在建筑构件内。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
