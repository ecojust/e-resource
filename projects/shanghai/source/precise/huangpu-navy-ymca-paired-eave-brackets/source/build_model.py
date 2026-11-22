"""Build the Shanghai Navy YMCA's paired brackets and upper chamfer from its 2016 street photograph."""
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
from top_floor import ID, PALETTE, add_building, texture

scope='依据2016年署名实照，表现海青大楼四川中路与香港路口白色顶层的两扇窗、深挑缘和成对曲托。'
META=dict(id=ID,name='海青大楼顶层双窗与成对弧形檐托',scope=scope,model_scope_zh=scope,
          viewer_page='navy-ymca-paired-eave-brackets.html',reference_height_m=3.468,all_dimensions_estimated=True,
          estimated='根据现场照片取相对尺寸；托臂的墙内锚固和绝对标高未测。')
if __name__ == '__main__':
    texture()
    build(source,META,PALETTE,add_building)
