"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from twin_arches import PALETTE,add_building
META={'id': 'hongkou-ramos-apartments-twin-arches', 'name': '拉摩斯公寓临街双拱窗与回纹窗楣', 'viewer_page': 'ramos-apartments-twin-arches.html', 'status': 'photo-informed-architectural-component', 'scope': '按2014年街景，选取临街立面中大券内的双拱窗、圆形浮饰、上下窗之间的矩形线脚及其下方五折回纹窗楣。', 'model_scope_zh': '按2014年街景，选取临街立面中大券内的双拱窗、圆形浮饰、上下窗之间的矩形线脚及其下方五折回纹窗楣。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-ramos-apartments-twin-arches/reference-review.json', 'estimated': 'Opening heights are relative to the photograph, depths and absolute widths are approximate.', 'coordinate_convention': 'x along the street elevation, outward -y, z upward from the cropped lower spandrel', 'copyright': 'Original model and materials under MIT.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
