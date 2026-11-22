"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from brick_arches import PALETTE,add_building
META={'id': 'huangpu-zizhong-424-426-paired-brick-arches', 'name': '自忠路424、426号临街二层双砖券与木窗', 'scope': '两块绿门牌上方的两跨红砖券。面街左侧426号为两扇合拢的百叶，右侧424号可见打开的木框、暗色窗洞。双跨之间的竖管经过券肩，白色凸窗台分别位于两窗下方。', 'model_scope_zh': '两块绿门牌上方的两跨红砖券。面街左侧426号为两扇合拢的百叶，右侧424号可见打开的木框、暗色窗洞。双跨之间的竖管经过券肩，白色凸窗台分别位于两窗下方。', 'estimated': '采用2020年街景球面转切面后按两处起拱点与窗台校准。两跨合计名义宽3.60米。照片能约束相对几何，开间、厚度和窗扇角度仍为估计。', 'viewer_page': 'zizhong-424-426-paired-brick-arches.html', 'interiors_modeled': False, 'coordinate_convention': 'Photo left to right is local X, Y points inward, Z is up. The window sill control is Z=0.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
