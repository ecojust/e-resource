"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from courtyard_screens import PALETTE,add_building
META={'id': 'pudong-qingxi-teahouse-courtyard-window-screens', 'name': '清溪茶馆内院三联木格压花玻璃窗', 'scope': '高桥镇清溪茶馆内院里，三扇相邻的棕色木窗各留两组完整的长方格。中央长玻璃通高，两侧小格各有一根短横梃。三道横带内各有两块矮玻璃，左窗呈暖黄色，向右逐渐显出灰蓝色。', 'model_scope_zh': '高桥镇清溪茶馆内院里，三扇相邻的棕色木窗各留两组完整的长方格。中央长玻璃通高，两侧小格各有一根短横梃。三道横带内各有两块矮玻璃，左窗呈暖黄色，向右逐渐显出灰蓝色。', 'estimated': '截取照片可完整辨认的上五排。单扇玻璃净宽估为0.445米。木框深度、玻璃表面压纹和未见的背面按可见反光近似刻画，真实尺寸待实测。', 'viewer_page': 'qingxi-teahouse-courtyard-window-screens.html', 'geometry_license': 'CC BY-SA 3.0', 'source_reference_only': True, 'copyright': '内院窗格见Fayhoo摄《Qingxi Chaguan》，2015年5月9日。蟋有的蟀2013年9月16日摄茶馆院门，题注同指东街20至22号。两照与此窗格模型按CC BY-SA 3.0署名。', 'photo_credit': '内院窗格见Fayhoo摄《Qingxi Chaguan》，2015年5月9日。蟋有的蟀2013年9月16日摄茶馆院门，题注同指东街20至22号。两照与此窗格模型按CC BY-SA 3.0署名。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:Qingxi_Chaguan.JPG', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/3.0/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 3.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
