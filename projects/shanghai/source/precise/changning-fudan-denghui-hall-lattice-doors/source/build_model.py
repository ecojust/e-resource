"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from lattice_doors import PALETTE,add_building
META={'id': 'changning-fudan-denghui-hall-lattice-doors', 'name': '复旦公学登辉堂正厅朱漆格扇', 'scope': '登辉堂正厅两扇相邻的朱漆格扇。上半扇的深色方格木棂留有通孔，下半扇为凹入的板心、抹头与边梃。', 'model_scope_zh': '登辉堂正厅两扇相邻的朱漆格扇。上半扇的深色方格木棂留有通孔，下半扇为凹入的板心、抹头与边梃。', 'estimated': '根据长宁区文化数字地图的正厅照片估算两扇合宽约1.18米，格扇通高约2.88米。格条的具体排法依可辨图形简化，边梃的进深、倒角和背侧属于估算。两端石鼓、上悬题匾、其余门扇、登辉堂西侧迁建的门楼及力学堂另留研究。', 'viewer_page': 'fudan-denghui-hall-lattice-doors.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
