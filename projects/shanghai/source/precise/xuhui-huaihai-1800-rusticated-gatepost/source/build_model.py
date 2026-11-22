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
from granite_post import ID, PALETTE, add_building, texture

scope='Antigng于2017年8月19日实拍的淮海中路1800号住宅入口，金褐色凹角牌写有1800和淮海中路，系在灰色毛面石柱前。石封顶呈小三角，两坡之下可见一块前突的多边石与后退的暗面。'
META=dict(id=ID,name='淮海中路1800号花岗石门柱与三角压顶',scope=scope,model_scope_zh=scope,viewer_page='huaihai-1800-rusticated-gatepost.html',reference_height_m=1.736,all_dimensions_estimated=True,estimated='第五批市表5D074登记住宅、现作办公。实照近大远小，本模型只取右侧石柱上段。各层石材与板厚依可见比例估计，墙内构造、石柱全高和院内建筑均未测绘。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
