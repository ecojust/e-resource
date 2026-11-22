"""Build the two-storey entrance corner shown in the 1952 workers' housing photograph."""
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
from entry import ID, PALETTE, add_building, texture

scope = '依据1952年8月《人民画报》“曹杨新村的工人住宅”照片，表现一处住宅转角的斜瓦门篷、楼梯高窗、外开启的侧窗及两跨坡屋。'
META = dict(id=ID, name='曹杨一村工人住宅折角门廊与窄窗', scope=scope,
            model_scope_zh=scope, viewer_page='caoyang-first-village-workers-entry.html',
            reference_height_m=5.96, all_dimensions_estimated=True,
            estimated='根据画报同期黑白照片取相对高宽。色彩及背面进深为示意，未取得栋号。')
if __name__ == '__main__':
    texture()
    build(source,META,PALETTE,add_building)
