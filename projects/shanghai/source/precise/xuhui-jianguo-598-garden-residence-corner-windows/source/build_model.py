"""Package the two storeys of steel corner windows at 598 Jianguo West Road."""
from pathlib import Path
import os
import sys

source = Path(__file__).resolve().parent
roots = list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0, Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tool_path = next(root/'tools' for root in roots if (root/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(tool_path))
from package_architectural_model import build
from corner import add_building, make_texture, PALETTE

ID = 'xuhui-jianguo-598-garden-residence-corner-windows'
META = {
    'id': ID,
    'name': '建国西路598号花园住宅临街转角钢窗与赭砖窗垛',
    'viewer_page': 'jianguo-598-corner-windows.html',
    'scope': '2018年同门牌照片中的两层临街转角钢窗、转角赭砖窗垛与水泥挑檐。',
    'model_scope_zh': '两层外墙局部。建筑物及院落的其余部分未作复原。',
    'reference_height_m': 5.84,
    'estimated': '窗宽、层高及出挑深度均按照片比例估计。',
    'source_register': f'source/precise/{ID}/reference-review.json',
    'copyright': 'Original mesh and procedural materials. Photographs cited as references.'
}
if __name__ == '__main__':
    make_texture(source/'roughcast.png')
    build(source, META, PALETTE, add_building)
