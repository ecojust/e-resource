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
from faceted_bays import ID, PALETTE, add_building, texture

scope='市表5A051简记绍兴路25号。高参88于2024年11月16日发表的图5拍到上海市人民政府铭牌「绍兴路25弄（1–4号）」，并注明1933年。取图4铁门后住宅上部两排格窗、两端凸窗及中部相连的双组横槽。'
META=dict(id=ID,name='绍兴路25弄住宅双折角凸窗与横槽窗间墙',scope=scope,model_scope_zh=scope,viewer_page='shaoxing-25-faceted-bays.html',reference_height_m=6.89,all_dimensions_estimated=True,estimated='铭牌记两幢住宅。图4能确认院内这面窗墙，但各户的门牌与单片窗之间尚无测量图。深度、绝对宽度与百叶槽回深按图估算。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
