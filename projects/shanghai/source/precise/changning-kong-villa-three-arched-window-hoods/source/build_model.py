"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from garden_hoods import PALETTE,add_building
META={'id': 'changning-kong-villa-three-arched-window-hoods', 'name': '孔氏别墅园侧高低三拱窗罩与曲线托臂', 'scope': '园侧底层深色窗框上方的三道白色拱罩，中央挑出的拱顶较高，两侧拱顶较低，曲线托臂自窗边向外挑起。', 'model_scope_zh': '园侧底层深色窗框上方的三道白色拱罩，中央挑出的拱顶较高，两侧拱顶较低，曲线托臂自窗边向外挑起。', 'estimated': '依据题名照片估整组三罩宽约3.2米。拱罩各自有外皮、薄前缘和内弧，四个支承轴按可见边线估算。照片下部受花木遮挡，窗下及室内留待实测。', 'viewer_page': 'kong-villa-three-arched-window-hoods.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
