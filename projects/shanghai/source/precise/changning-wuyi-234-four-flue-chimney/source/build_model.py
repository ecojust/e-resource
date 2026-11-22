"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from four_flues import PALETTE,add_building
META={'id': 'changning-wuyi-234-four-flue-chimney', 'name': '武夷路234号住宅中央屋坡四孔砖烟囱', 'scope': '在面向花园的中央屋坡上，四个浅色圆形烟口排在长方形砖烟囱顶上。两道竖缝把长面分成三段；上部连续数层挑砖，最上一圈砖竖砌。', 'model_scope_zh': '在面向花园的中央屋坡上，四个浅色圆形烟口排在长方形砖烟囱顶上。两道竖缝把长面分成三段；上部连续数层挑砖，最上一圈砖竖砌。', 'estimated': '四个烟口及其排列在2018年署名原照中能够逐个辨认。砖层以一皮砖含灰缝名义74毫米估算尺寸。烟道内部只展示口沿以下一小段，隐蔽深度和背面按可见表面推定。', 'viewer_page': 'wuyi-234-four-flue-chimney.html', 'source_reference_only': False, 'geometry_license': 'CC BY-SA 4.0', 'copyright': 'Antigng, 武夷路234号, 2018-02-13. Architectural geometry derived from the photograph under CC BY-SA 4.0.', 'photo_credit': 'Antigng, 武夷路234号, 2018-02-13. Architectural geometry derived from the photograph under CC BY-SA 4.0.', 'photo_source': 'https://commons.wikimedia.org/wiki/File:%E6%AD%A6%E5%A4%B7%E8%B7%AF234%E5%8F%B7.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0/'}

if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 4.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
