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
from arched_recess import ID, PALETTE, add_building, texture

scope='取Antigng在2018年1月28日拍摄的21号住宅墙面。较低的瓦檐覆盖狭长圆头开口，后方高墙的浅色檐带下有一排圆弧缺口。'
META=dict(id=ID,name='新闸路1340弄21号圆头深窗洞与重檐',scope=scope,model_scope_zh=scope,viewer_page='xinzha-1340-no21-arched-recess.html',reference_height_m=5.91,all_dimensions_estimated=True,estimated='树叶遮住开口下半部分，照片只支持上段的拱顶、深侧墙和凹进的表面。模型在树冠遮挡线附近截取洞内；深度与墙厚由照片可见阴影估计。名录现用名为经济日报上海记者站。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
