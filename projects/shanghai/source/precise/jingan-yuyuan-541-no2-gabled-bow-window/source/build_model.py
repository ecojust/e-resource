"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from gable_and_shutters import PALETTE,add_building
META={'id': 'jingan-yuyuan-541-no2-gabled-bow-window', 'name': '愚园路541弄2号木构山墙与弧窗百叶', 'scope': '半木构山墙的两道宽梁和竖木，阁楼双扇各三片玻璃。下部凸窗的四组浅色百叶随弧转向，窗头、窗台和中间石框有不同出挑。右端被枝叶挡住，保留相片中能辨的外沿。', 'model_scope_zh': '半木构山墙的两道宽梁和竖木，阁楼双扇各三片玻璃。下部凸窗的四组浅色百叶随弧转向，窗头、窗台和中间石框有不同出挑。右端被枝叶挡住，保留相片中能辨的外沿。', 'estimated': '名义山墙宽4.1米；木框用照片像素迹线，凸窗半径1.82米为近似。右侧百叶细部有树遮挡，同组叶距参考中央两组。', 'viewer_page': 'yuyuan-541-no2-gabled-bow-window.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the visible facade, Y points inward, and Z points up.'}

CREDIT = 'Antigng, 2018-02-13, Wikimedia Commons. The window framing, visible rail or timber members are measurements and original modelling based on that photograph.'
PAGE = 'https://commons.wikimedia.org/wiki/File:%E6%84%9A%E5%9B%AD%E8%B7%AF541%E5%BC%842%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg'
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
