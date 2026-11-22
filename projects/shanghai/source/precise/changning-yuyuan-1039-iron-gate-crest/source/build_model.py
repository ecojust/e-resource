"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from scroll_gate import PALETTE,add_building
META={'id': 'changning-yuyuan-1039-iron-gate-crest', 'name': '愚园路1039号院门弧形上框与卷叶铁花', 'scope': '院门上的两道弧形铁框之间填以卷铁花，最上方另有一列高低参差的花梢。从画面左边门柱到右边扇首，可以辨认铁叶、顶上的长弯枝以及下方实心门板的上缘。', 'model_scope_zh': '院门上的两道弧形铁框之间填以卷铁花，最上方另有一列高低参差的花梢。从画面左边门柱到右边扇首，可以辨认铁叶、顶上的长弯枝以及下方实心门板的上缘。', 'estimated': '采用2018年2月10日的门扇外观，安装与更换年代未知。门宽按2.12米估算，扁铁的厚度、叶尾和背面的连接按可见轮廓推定。宿屋上层转角钢窗已有独立记录。', 'viewer_page': 'yuyuan-1039-iron-gate-crest.html', 'geometry_license': 'CC BY-SA 4.0', 'source_reference_only': True, 'copyright': 'Antigng，《愚园路1039号住宅》，2018年2月10日，Wikimedia Commons，CC BY-SA 4.0。三维曲线按照片中门扇的铁花重新绘制。', 'photo_credit': 'Antigng，《愚园路1039号住宅》，2018年2月10日，Wikimedia Commons，CC BY-SA 4.0。三维曲线按照片中门扇的铁花重新绘制。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:%E6%84%9A%E5%9B%AD%E8%B7%AF1039%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/4.0/'}
if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 4.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
