"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from wing_window import PALETTE,add_building
META={'id': 'hongkou-guangdong-theatre-arched-window-bay', 'name': '广东大戏院临街右翼三层窗带与砖券', 'viewer_page': 'guangdong-theatre-arched-window-bay.html', 'status': 'photo-informed-architectural-component', 'scope': '群众影剧院四川北路1552号修缮后正立面，取观者右边一条三层窗带，左右裁至褐色面砖，上至窗带上方的一段阶梯横檐。', 'model_scope_zh': '群众影剧院四川北路1552号修缮后正立面，取观者右边一条三层窗带，左右裁至褐色面砖，上至窗带上方的一段阶梯横檐。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-guangdong-theatre-arched-window-bay/reference-review.json', 'estimated': 'Opening heights are relative to the photograph, depths and absolute widths are approximate.', 'coordinate_convention': 'x along the street elevation, outward -y, z upward from the cropped lower spandrel', 'copyright': 'Original model and materials under MIT.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
