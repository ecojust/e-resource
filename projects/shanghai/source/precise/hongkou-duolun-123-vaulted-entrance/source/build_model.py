"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from vaulted_canopy import PALETTE,add_building
META={'id': 'hongkou-duolun-123-vaulted-entrance', 'name': '多伦路123号老电影咖啡馆四柱拱廊与分格券底', 'scope': '入口前后两对圆柱、带座托的柱脚、弧形金属顶和多道浅色前券共同围出门廊；仰看券底可辨纵肋、横格和每格中部浅饰。', 'model_scope_zh': '入口前后两对圆柱、带座托的柱脚、弧形金属顶和多道浅色前券共同围出门廊；仰看券底可辨纵肋、横格和每格中部浅饰。', 'estimated': '2019年虹口发布文章说明1999年改建为咖啡馆。模型记录2015年和2024年两张署名照中共同可见的现状门廊。前柱轴距取名义2.12米，顶板、浅饰和石脚尺寸由照片估计。', 'viewer_page': 'duolun-123-vaulted-entrance.html', 'source_reference_only': True, 'geometry_license': 'CC BY-SA 4.0', 'copyright': 'CC BY-SA 4.0. Windmemories，《20240107 123 Duolun Road.jpg》，CC BY-SA 4.0；Fayhoo，《Laodianying Kafeiguan.JPG》，2015年4月12日，CC BY-SA 3.0。两照出自Wikimedia Commons；模型据其可见柱列和券底重新绘制。', 'photo_credit': 'Windmemories，《20240107 123 Duolun Road.jpg》，CC BY-SA 4.0；Fayhoo，《Laodianying Kafeiguan.JPG》，2015年4月12日，CC BY-SA 3.0。两照出自Wikimedia Commons；模型据其可见柱列和券底重新绘制。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:20240107_123_Duolun_Road.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0/'}

if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 4.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
