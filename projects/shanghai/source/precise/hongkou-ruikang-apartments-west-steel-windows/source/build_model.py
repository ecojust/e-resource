"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from steel_windows import PALETTE,add_building
META={'id': 'hongkou-ruikang-apartments-west-steel-windows', 'name': '瑞康公寓四川北路西立面三联钢窗与砖柱', 'viewer_page': 'ruikang-west-steel-windows.html', 'status': 'photo-informed-architectural-component', 'scope': '四川北路18号，西面街墙中段的一组三扇钢格窗，含浅色窗下板、四道砖墩和三段外挑砖窗楣。', 'model_scope_zh': '四川北路18号，西面街墙中段的一组三扇钢格窗，含浅色窗下板、四道砖墩和三段外挑砖窗楣。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-ruikang-apartments-west-steel-windows/reference-review.json', 'estimated': 'Window spans, sill and brick reveals estimated from dated street images.', 'coordinate_convention': 'Horizontal x, outward -y, vertical z. Zero is the lower cut through the window apron.', 'copyright': 'Original model and materials under MIT.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
