"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from warehouse_bay import PALETTE,add_building
META={'id': 'huangpu-south-suzhou-warehouse-1929-tablet', 'name': '南苏州路955号仓库临河立面的1929纪年牌与钢窗', 'scope': '临河砖墙上方的浅石纪年牌，上宽下窄，两侧各有一小方脚。牌面上深色的1929数字与下面实心过梁、深进的横列钢窗及凸出的窗台一起展出。', 'model_scope_zh': '临河砖墙上方的浅石纪年牌，上宽下窄，两侧各有一小方脚。牌面上深色的1929数字与下面实心过梁、深进的横列钢窗及凸出的窗台一起展出。', 'estimated': '按照2015年的具名照片估算开窗约宽2.96米，以窗洞、牌面及数字的相对尺寸确定比例；墙深、数字凸起程度、窗后玻璃和玻璃分片为近似。', 'viewer_page': 'south-suzhou-warehouse-1929-tablet.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
