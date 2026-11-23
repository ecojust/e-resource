"""Build the documented entrance and courtyard facade at 202 South Shaanxi Road, Shanghai."""
import argparse
from pathlib import Path
import json
import sys
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
from photo_architecture import Builder as PlainBuilder
import courtyard_front, entrance, open_balustrades, stone_guardians, pendant_emission
import finish_surfaces, west_wing_and_roof
ID='xuhui-shaanxi-202-former-yihe-hospital'
SLUG='shaanxi-202-former-yihe-hospital'
META=dict(id=ID,name='怡和医院旧址庭院立面与拱顶门廊',address='上海市徐汇区陕西南路202号',heritage_group='5D079',
          source='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          photo_source='https://commons.wikimedia.org/wiki/File:Shanghai_Jiaoyu_Pingguyuan.JPG',
          photo_author='Fayhoo / 高参88',photographer='Fayhoo / 高参88',geometry_license='MIT',texture_license='MIT',
          photos_embedded=False,viewer_page=SLUG+'.html',scope='陕西南路202号院内主楼朝庭院的六轴立面，拱形门廊、石狮与能由相片复核的西侧翼。')
if (HERE/'cameras.json').is_file():
    META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())
PALETTE={**courtyard_front.PALETTE,**entrance.PALETTE,**open_balustrades.PALETTE,**stone_guardians.PALETTE,**west_wing_and_roof.PALETTE,**finish_surfaces.PALETTE}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material="limestone",label="detail"):
        PlainBuilder.add(self,vertices,faces,material,label)
        if material in finish_surfaces.SURFACES:
            finish_surfaces.map_finish(self.parts[-1])

    def save(self,path,metadata=None):
        if not any(self.palette[p["material"]].get("texture") for p in self.parts):
            report=PlainBuilder.save(self,path,metadata)
        else:
            super().save(path,metadata)
            report=finish_surfaces.embed_normals(path)
        return pendant_emission.bind(path,report)
def add_building(b,lod=False):
    courtyard_front.add_courtyard_front(b,lod)
    entrance.add_entrance(b,lod)
    open_balustrades.add_balustrades(b,lod)
    stone_guardians.add_guardians(b,lod)
    west_wing_and_roof.add_west_wing_and_roof(b,lod)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--lod',action='store_true')
    args=parser.parse_args()
    b=Builder(PALETTE);add_building(b,args.lod)
    print(b.save(args.output,META)['sha256'])
