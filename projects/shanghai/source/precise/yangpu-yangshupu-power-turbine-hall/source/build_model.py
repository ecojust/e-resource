"""Package the elevations seen together in the 1926 Yangshupu works photograph."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photographed_works import PALETTE, factory_elevations

ID = 'yangpu-yangshupu-power-turbine-hall'
NAME = '杨树浦电厂汽机房及4号锅炉房（1926年合影可见外观）'
SCOPE = '取1926年合影及1935年同侧照片共同可见的长翼排窗、突出竖墩、折返檐线、高冠端部、烟筒与弧形屋架。被前景遮挡的底层、照片背面及各翼厂房名称留待核实。'
META = {
    'id': ID, 'name': NAME, 'viewer_page': 'yangshupu-turbine-hall.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'reference_height_m': 33.7,
    'estimated': '窗跨、屋冠及烟筒依照片比例估算；黑白影像不足以确定外墙原色。三维单体仅作历史立面研究。',
    'status': 'historical-photo-informed-facade-study',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'coordinate_convention': 'Photo-relative local coordinates in metres. X runs along the main window wall toward the projecting crown, Y recedes from its long elevation. The whole model is turned toward the comparison camera. No photogrammetric coordinates are assigned to the present site.',
    'interiors_modeled': False,
    'copyright': 'Original procedural architectural geometry. Photographic documentation is linked externally. The delivered files contain no photographic pixels or third-party meshes.',
}

if __name__ == '__main__':
    build(HERE, META, PALETTE, factory_elevations)
