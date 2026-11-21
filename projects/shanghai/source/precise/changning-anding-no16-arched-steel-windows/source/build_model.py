"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from paired_sash import PALETTE,add_building
META={'id': 'changning-anding-no16-arched-steel-windows', 'name': '安定坊16号双券钢窗与弧饰窗台', 'viewer_page': 'anding-no16-arched-steel-windows.html', 'scope': '16号朝院一侧二层的成对半圆券格窗、共用石色窗台及其弧饰下缘与灰褐粗粒墙面。', 'model_scope_zh': '16号朝院一侧二层的成对半圆券格窗、共用石色窗台及其弧饰下缘与灰褐粗粒墙面。', 'status': 'photo-informed-architectural-component', 'estimated': '两窗各按约0.97米宽设比，依据照片估算。窗框表面按照片作深色金属处理，墙面颗粒为程序生成。', 'interiors_modeled': False, 'coordinate_convention': 'X runs along the paired windows, positive Y points behind the wall and Z is up. Distances in metres.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
