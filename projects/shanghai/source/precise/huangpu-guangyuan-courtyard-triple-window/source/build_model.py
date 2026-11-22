"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from courtyard_lights import PALETTE,add_building
META={'id': 'huangpu-guangyuan-courtyard-triple-window', 'name': '光远坊内院三联木窗与分层窗台', 'scope': '内院照片中的一组三联木窗，含两根深色木梃、凸出的双层窗台、窗下浅圆饰和两侧墙面分格。', 'model_scope_zh': '内院照片中的一组三联木窗，含两根深色木梃、凸出的双层窗台、窗下浅圆饰和两侧墙面分格。', 'estimated': '窗洞宽约1.72米、净高约1.21米。比例来自改造前的内院题图，绝对高程、做法和构件深度待现场实测。', 'viewer_page': 'guangyuan-courtyard-triple-window.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
