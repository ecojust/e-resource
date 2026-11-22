"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from curved_sash import PALETTE,add_building
META={'id': 'jingan-xinzha-1378-no17-curved-steel-window', 'name': '新闸路1378弄17号弧形钢窗与露台铁栏', 'scope': '临院的一段弧形钢窗。可见八列宽窄不一的窗面，一根深色横档划分上下两排。窗前是浅色凸窗台，露台左端留有弯铁撑与砖挑头；右侧树后没有可辨栏杆。', 'model_scope_zh': '临院的一段弧形钢窗。可见八列宽窄不一的窗面，一根深色横档划分上下两排。窗前是浅色凸窗台，露台左端留有弯铁撑与砖挑头；右侧树后没有可辨栏杆。', 'estimated': '模型弧窗高约1.50米、名义半径2.36米，由单张斜照片估计；端部与树后墙面没有测绘依据。玻璃的灰绿明暗为原创材料。', 'viewer_page': 'xinzha-1378-no17-curved-steel-window.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the visible facade, Y points inward, and Z points up.'}

CREDIT = 'Antigng, 2018-01-28, Wikimedia Commons. The window framing, visible rail or timber members are measurements and original modelling based on that photograph.'
PAGE = 'https://commons.wikimedia.org/wiki/File:%E6%96%B0%E9%97%B8%E8%B7%AF1378%E5%BC%8417%E5%8F%B7.jpg'
LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0/'
GEOMETRY_LICENSE = 'CC BY-SA 4.0'
META.update(copyright='CC BY-SA 4.0. ' + CREDIT, geometry_license=GEOMETRY_LICENSE,
            photo_credit=CREDIT, photo_source=PAGE, derivative_license_url=LICENSE)

if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license=GEOMETRY_LICENSE)
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
