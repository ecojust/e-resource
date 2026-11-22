"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from carving_rights import write_metadata
from library_pier import PALETTE,add_building
META={'id': 'jingan-customs-library-stone-roundel', 'name': '江海图书馆海关楼门侧石徽与斜带束柱', 'scope': '取海关楼入口画面左侧石墩上部。方凹框内的圆形雕饰带双层石边；两侧各有一束细棱，由三道斜束带箍起，上方多道水平石线向外挑出。', 'model_scope_zh': '取海关楼入口画面左侧石墩上部。方凹框内的圆形雕饰带双层石边；两侧各有一束细棱，由三道斜束带箍起，上方多道水平石线向外挑出。', 'estimated': '据2018年两张正反斜照和2025年报道的正面照片量取可见比例。石墩名义宽1.44米；石徽表面参照原照局部明暗，雕刻深度未实测，模型所示仅为近似起伏。', 'viewer_page': 'customs-library-stone-roundel.html', 'source_reference_only': False, 'geometry_license': 'Stone medallion adapted from Antigng’s photograph: CC BY-SA 4.0. Original surrounding stonework, procedural model and code: MIT.', 'copyright': 'Antigng，2018年1月28日，《静安区图书馆海关楼 1、2》，Wikimedia Commons，CC BY-SA 4.0。石徽起伏据第一张原照裁切、校平光照并转成几何，保留相同许可。', 'photo_credit': 'Antigng，2018年1月28日，《静安区图书馆海关楼 1、2》，Wikimedia Commons，CC BY-SA 4.0。石徽起伏据第一张原照裁切、校平光照并转成几何，保留相同许可。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:%E9%9D%99%E5%AE%89%E5%8C%BA%E5%9B%BE%E4%B9%A6%E9%A6%86%E6%B5%B7%E5%85%B3%E6%A5%BC_1.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0'}
if __name__=="__main__":
    write_metadata(package)
    package.build(SOURCE,META,PALETTE,add_building)
