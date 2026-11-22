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
from door_and_steps import ID, PALETTE, add_building, texture

scope='Fayhoo于2016年2月10日在虬江路1057号拍摄了红砖长楼临庭院的一面。模型取画面右端的双扇玻璃门、浅色门楣、三级踏步与台旁小通气口。'
META=dict(id=ID,name='上海铁道医院虬江路红砖长楼玻璃门与三级踏步',scope=scope,model_scope_zh=scope,viewer_page='railway-hospital-brick-door-and-steps.html',reference_height_m=2.85,all_dimensions_estimated=True,estimated='取照片右端开口。端部方位未经现场罗盘复测。台阶的踏深、墙厚和金属截面按可见比例推定。双扇玻璃上红色圆形标记可辨，标内纹字未辨。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
