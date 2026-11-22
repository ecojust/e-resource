"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from three_arches import PALETTE,add_building
META={'id': 'changning-fan-garden-no8-three-arched-windows', 'name': '范园8号李铭住宅三联券窗与波形老虎窗', 'scope': '2002年照片中8号主立面顶层三樘券窗、窗下浅饰板、坡顶陶瓦与中央波形老虎窗。', 'model_scope_zh': '2002年照片中8号主立面顶层三樘券窗、窗下浅饰板、坡顶陶瓦与中央波形老虎窗。', 'estimated': '三联窗所在墙的宽度按比例估计为4.64米。红瓦坡面和压顶的进深由斜视比例估计；建筑底楼、两翼及相邻10号均在模型范围以外。', 'viewer_page': 'fan-garden-no8-three-arched-windows.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
