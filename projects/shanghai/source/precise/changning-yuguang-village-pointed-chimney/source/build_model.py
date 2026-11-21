"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from chimney import PALETTE,add_building
META={'id': 'changning-yuguang-village-pointed-chimney', 'name': '渔光邨尖顶烟囱与三联排烟孔', 'viewer_page': 'yuguang-village-pointed-chimney.html', 'scope': '屋顶浅色粗粒抹面烟囱。长面三条高低错落的尖券排烟孔，端面一孔，下接方筒与折边金属泛水。', 'model_scope_zh': '屋顶浅色粗粒抹面烟囱。长面三条高低错落的尖券排烟孔，端面一孔，下接方筒与折边金属泛水。', 'estimated': '长面1.4米，窄面0.5米，建模高度约2米，均按照片比例估计。排烟孔外轮廓与抹面可辨，烟道内部深度未有施工图可核。', 'interiors_modeled': False, 'coordinate_convention': 'X follows the three openings along the long face, Y points into the chimney and Z is upward. Dimensions are in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
