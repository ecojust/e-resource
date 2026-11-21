"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from timber_gable import PALETTE,add_building
META={'id': 'xuhui-yueyang-former-french-consulate-timber-gable', 'name': '原法国领事馆岳阳路11号楼露木山墙与双窗', 'viewer_page': 'yueyang-consulate-timber-gable.html', 'status': 'photo-informed-architectural-component', 'scope': '岳阳路319号11号楼中央凸出部分的上层双窗、白色灰墙、外露木构、九条弯托、三角山墙及窄挑檐。', 'model_scope_zh': '岳阳路319号11号楼中央凸出部分的上层双窗、白色灰墙、外露木构、九条弯托、三角山墙及窄挑檐。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-yueyang-former-french-consulate-timber-gable/reference-review.json', 'estimated': '建筑没有公开测绘尺。米制尺寸按常见窗宽估计，玻璃分隔、弯托进深、边瓦厚度均为近似值。', 'coordinate_convention': 'Horizontal x, facade plane y=0, vertical z. Local zero marks the lower cut below the two upstairs windows.', 'copyright': 'Original modelling and materials under MIT. Photography credited to CyberCop and Eecc.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
