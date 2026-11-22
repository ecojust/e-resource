"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
import package_architectural_model as package
from arched_sashes import PALETTE,add_building
META={'id': 'hongkou-shanyin-274-paired-brick-arches', 'name': '山阴路274弄住宅成对红砖券窗与木格上亮', 'scope': '弄内实照左侧的上层窗列，选其中相连两樘。红砖窗橛、放射砖券、半圆上亮、下部红漆玻璃木框与外挑浅石窗台分别建模。', 'model_scope_zh': '弄内实照左侧的上层窗列，选其中相连两樘。红砖窗橛、放射砖券、半圆上亮、下部红漆玻璃木框与外挑浅石窗台分别建模。', 'estimated': '依Fayhoo的2015年弄内照片量读两樘可见的券窗。以净宽约1.00米作比例尺；树枝挡住的木格、灰缝、砖券厚度与窗后进深为估计。单幅照片未把窗列落实到某一户。', 'viewer_page': 'shanyin-274-paired-brick-arches.html', 'source_reference_only': True, 'geometry_license': 'CC BY-SA 3.0', 'copyright': 'CC BY-SA 3.0. Fayhoo，《Shanyinlu 274 Long.JPG》，2015年4月12日，Wikimedia Commons，CC BY-SA 3.0。模型据可见窗列重新绘制。', 'photo_credit': 'Fayhoo，《Shanyinlu 274 Long.JPG》，2015年4月12日，Wikimedia Commons，CC BY-SA 3.0。模型据可见窗列重新绘制。', 'photo_source': 'https://commons.wikimedia.org/wiki/File:Shanyinlu_274_Long.JPG', 'derivative_license_url': 'https://creativecommons.org/licenses/by-sa/3.0/'}

if __name__ == '__main__':
    write_json = package.write_json
    def write_with_rights(path,value):
        if path.name=='manifest.json':
            value=dict(value,geometry_license='CC BY-SA 3.0')
        write_json(path,value)
    package.write_json=write_with_rights
    package.build(SOURCE,META,PALETTE,add_building)
