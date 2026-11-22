"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from campus_belfry import PALETTE,add_building
META={'id': 'pudong-yangjing-school-historic-bell-pavilion', 'name': '洋泾中学旧办公楼前四柱钟亭与铜校钟', 'scope': '潍坊路111号校史馆（1947年旧办公楼）前的青铜校钟挂在一座四柱亭内。四根方形深色木柱向上收拢，支着短横梁、方形檐口和低矮的斜坡顶。钟肩向下缓收，钟腹在钟口处外张，口沿内可见悬出的钟舌。', 'model_scope_zh': '潍坊路111号校史馆（1947年旧办公楼）前的青铜校钟挂在一座四柱亭内。四根方形深色木柱向上收拢，支着短横梁、方形檐口和低矮的斜坡顶。钟肩向下缓收，钟腹在钟口处外张，口沿内可见悬出的钟舌。', 'estimated': '依据学校在2021年发出的两幅图。钟亭和校钟的总高与开间按图像比例估算，方亭名义高2.69米。铜钟的内部厚度、不可见的挂件、木构背面及屋面背坡为推测。钟亭建造年份待考。', 'viewer_page': 'yangjing-school-historic-bell-pavilion.html', 'geometry_license': 'MIT', 'source_reference_only': True, 'copyright': '照片与沿革据上海市洋泾中学供稿的浦东教育巡展（2021年5月11日）。2016年中国青年网的校史报道提供复校背景。原照片只作研究观察，模型采用原创几何与材质。', 'photo_credit': '照片与沿革据上海市洋泾中学供稿的浦东教育巡展（2021年5月11日）。2016年中国青年网的校史报道提供复校背景。原照片只作研究观察，模型采用原创几何与材质。', 'photo_source': 'https://www.shangnaxue.net/a/1400625199730200577?cid=101', 'derivative_license_url': 'https://opensource.org/license/mit/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='MIT')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
