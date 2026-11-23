"""Build the documented exterior of 196 Kangping Road. Dimensions are local to the photographed elevation."""
import argparse,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))] if (p/'tools/package_architectural_model.py').is_file())
for path in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.append(str(PROJECT/'source/precise'/path))
from crown_builder import CrownBuilder
from materials import PALETTE,WALL
from placement import Facade
from street_front import add_street_front
from rear_elevation import add_rear_elevation
class Builder(CrownBuilder):
    def add(self, vertices, faces, material='limestone', label='detail'):
        super().add(vertices,faces,material,label)
        if material==WALL:
            part=self.parts[-1]
            # The street plaster has approximately 0.40 m courses and 1.5 m rectangular panels.
            part['texcoords']=[[u*.84,v*.80] for u,v in part['texcoords']]

ID='xuhui-kangping-196-shuttered-residence';SLUG='kangping-196-shuttered-residence'
META={'id':ID,'name':'康平路196号住宅百叶窗与灰塑','address':'上海市徐汇区康平路196号','heritage_group':'5D031','period':'以2019年具名街道外观和补充的公开窗缘量测为依据','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html','photo_source':'https://commons.wikimedia.org/wiki/File:196_Kangping_Road.jpg','viewer_page':SLUG+'.html','scope':'带百叶窗、灰塑与叠檐的历史建筑街道外观；作品采用局部坐标。'}
META['camera_views']=json.loads((HERE/'cameras.json').read_text())
def add_building(b,lod=False):
    f=Facade(b)
    add_street_front(f,lod)
    add_rear_elevation(f,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(parents=True,exist_ok=True);r=b.save(a.output,META);print(r['parts'],r['triangles'],r['sha256'])
