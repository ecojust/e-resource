"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from octagon import PALETTE,add_building
META={'id': 'changning-wuyi-154-octagonal-attic', 'name': '武夷路154号住宅八角砖券阁窗与檐下立砖', 'scope': '主楼檐下留有一扇八角小窗。八条边分别用顺着券线的砖块围合，一根深色窗梃横过窗洞。上方的两道立砖从红砖墙面挑出，檐底另有一道阴影。斜顶在右下角遮住一部分墙体。', 'model_scope_zh': '主楼檐下留有一扇八角小窗。八条边分别用顺着券线的砖块围合，一根深色窗梃横过窗洞。上方的两道立砖从红砖墙面挑出，檐底另有一道阴影。斜顶在右下角遮住一部分墙体。', 'estimated': '依据2018年可核实的原照量取八个角与檐带。砖皮高度提供名义比例；单张照片不能量出砖券厚度、窗扇前后距离或屋顶背面。', 'viewer_page': 'wuyi-154-octagonal-attic.html', 'source_reference_only': False, 'geometry_license': 'CC BY-SA 4.0', 'copyright': 'Antigng, 武夷路154号住宅, 2018-02-13. Architectural geometry derived from the photograph under CC BY-SA 4.0.', 'photo_credit': 'Antigng, 武夷路154号住宅, 2018-02-13. Architectural geometry derived from the photograph under CC BY-SA 4.0.', 'photo_source': 'https://commons.wikimedia.org/wiki/File:%E6%AD%A6%E5%A4%B7%E8%B7%AF154%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0/'}

if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 4.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
