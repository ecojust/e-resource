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
from lane_gate import ID, PALETTE, add_building, texture

scope='2017年8月19日Antigng拍摄的五原路76弄住宅入口，门柱绿牌写有“76弄1–16号 五原路”。内侧铁门的两道曲线顶栏间有环与菱芯，门右侧窄条用连续卷铁装饰。'
META=dict(id=ID,name='华邨五原路76弄起伏铁门与弄牌',scope=scope,model_scope_zh=scope,viewer_page='hua-cun-lane76-waved-iron-gate.html',reference_height_m=2.265,all_dimensions_estimated=True,estimated='5D070原名华邸，现名华邨。本件只截取照片所见的弄牌、相邻墙段及铁门上部；照片不能给门扇的建造年份，底部裁切处、漆层厚度、铁条尺寸亦无实测。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
