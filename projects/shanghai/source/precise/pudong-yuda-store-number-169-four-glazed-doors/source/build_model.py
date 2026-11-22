"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from entrance_panels import PALETTE,add_building
META={'id': 'pudong-yuda-store-number-169-four-glazed-doors', 'name': '裕大南货店新场大街169号四扇木门与石门枕', 'scope': '临街169号门口有四扇深褐色木框门。每扇门的上部在蓝灰玻璃前嵌折线回纹，中间留方形色玻璃；下部镶浅浮雕木板。中间两扇略向街面打开，接缝处有一对铜环。门槛两端各有一个前端削圆的石门枕。', 'model_scope_zh': '临街169号门口有四扇深褐色木框门。每扇门的上部在蓝灰玻璃前嵌折线回纹，中间留方形色玻璃；下部镶浅浮雕木板。中间两扇略向街面打开，接缝处有一对铜环。门槛两端各有一个前端削圆的石门枕。', 'estimated': '据2023年7月4日已刊实照。四扇门名义合宽约2米，门扇厚度、门枕背面及中扇开启角约7.5度与10度为图像估计。铭牌记载该幢房屋完工于1931年，现存门料及玻璃的安装年代待查。', 'viewer_page': 'yuda-store-number-169-four-glazed-doors.html', 'geometry_license': 'MIT', 'source_reference_only': True, 'copyright': '上海东北任，《新场古镇的俚舍》，页面于2023年7月4日更新。门侧上海市人民政府公布的铭牌实录“新场镇新场大街169–173号（单号）”和1931年竣工。照片用于研究，模型采用原创几何和材质。', 'photo_credit': '上海东北任，《新场古镇的俚舍》，页面于2023年7月4日更新。门侧上海市人民政府公布的铭牌实录“新场镇新场大街169–173号（单号）”和1931年竣工。照片用于研究，模型采用原创几何和材质。', 'photo_source': 'https://www.meipian.cn/4tgweyqm', 'derivative_license_url': 'https://opensource.org/license/mit/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='MIT')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
