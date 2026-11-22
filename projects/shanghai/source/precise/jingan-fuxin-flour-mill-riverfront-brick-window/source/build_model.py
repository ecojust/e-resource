"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from factory_window import PALETTE,add_building
META={'id': 'jingan-fuxin-flour-mill-riverfront-brick-window', 'name': '福新面粉一厂沿河厂房红砖壁柱与矩形窗', 'scope': '沿河三层厂房上部的一跨窗墙，红砖壁柱与浅褐砖墙交接，矩形窗上方设砖过梁，窗底石台向外挑出。', 'model_scope_zh': '沿河三层厂房上部的一跨窗墙，红砖壁柱与浅褐砖墙交接，矩形窗上方设砖过梁，窗底石台向外挑出。', 'estimated': '取沿河三层厂房上层单跨，区分后排六层钢筋混凝土建筑。宽约3.0米、高约3.1米和各构件进深均据实景照片估算。', 'viewer_page': 'fuxin-flour-mill-riverfront-brick-window.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
