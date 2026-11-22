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
from portal_and_aggregate import ID, PALETTE, add_building, texture

scope='徐汇文旅2021年3月的《1号楼抢先看》照片中，“1号楼”标字就在鹅卵石墙面上。其左侧门套有两枚扁圆饰，往上接门柱的折线柱头和向外逐级挑出的收边。本作截取门楣右部与旁边一小段干粘石外墙。'
META=dict(id=ID,name='上海京剧传习馆1号楼鹅卵石墙与门楣双圆饰',scope=scope,model_scope_zh=scope,viewer_page='yueyang-168-jingju-pebble-dash-doorhead.html',reference_height_m=1.49,all_dimensions_estimated=True,estimated='5D042登记岳阳路168弄1号、2号楼。本作仅依能指明1号楼的门套近景。原照仅见门的一段，模型高度为截取范围，石粒颜色受光照影响，粒径、圆饰厚度和挑出长度均为估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
