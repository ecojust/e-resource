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
from portal import ID, PALETTE, add_building, texture

scope='依据Livelikerw在2019年7月11日拍摄的广东路街景，取右拱脚有绿色131弄铭牌的通道入口。造型包括水平分缝、扇形券石、转折的石雕卷托及券底阴影。'
META=dict(id=ID,name='广东路131弄券门与卷形拱心石',scope=scope,model_scope_zh=scope,viewer_page='guangdong-131-scroll-keystone.html',reference_height_m=4.24,all_dimensions_estimated=True,estimated='左起毗邻商铺的蓝色门牌为广东路123号。券口右侧带131弄绿牌，能确定通道所在；两侧大部分内墙被电缆、车辆及行人遮挡。券宽、进深、背面和卷托外伸按图估算，缺少绝对坐标。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
