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
from oculus_and_brickwork import ID, PALETTE, add_building, texture

scope='取陕西北路80号瑞士国总领事馆旧址的灰砖山墙中段，重建阁楼中央百叶圆窗、石圈和上接三角线条。'
META=dict(id=ID,name='瑞士国总领事馆旧址阁楼百叶圆窗与石饰圈',scope=scope,model_scope_zh=scope,viewer_page='swiss-consulate-louvred-oculus.html',reference_height_m=2.52,all_dimensions_estimated=True,estimated='窗径、深度和石材色值为单张斜向照片估算。原图能辨水平百叶的方向，暗部的叶片总数不可逐一确认。所在院墙、楼侧入口与场地绝对位置未纳入。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
