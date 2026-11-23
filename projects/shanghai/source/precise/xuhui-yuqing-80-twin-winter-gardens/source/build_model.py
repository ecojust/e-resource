"""Build the photographically documented garden elevation of 80 Yuqing Road in Shanghai."""
import argparse
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
from central_front import PALETTE as CENTRAL, add_central_front
from garden_finishes import PALETTE as FINISHES, map_finish, embed_normals

from winter_gardens import PALETTE as GARDENS, add_winter_gardens
from northeast_ground_windows import add_northeast_ground
from southwest_colonnade import PALETTE as SOUTHWEST, add_southwest_colonnade

ID='xuhui-yuqing-80-twin-winter-gardens'
SLUG='yuqing-80-twin-winter-gardens'
PALETTE={**SOUTHWEST,**CENTRAL,**GARDENS,**FINISHES}
META=dict(id=ID,name='余庆路80号双圆阳光房花园立面',address='上海市徐汇区余庆路80号',
          heritage_group='5D075',source='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          photo_source='https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480102ze0a.html',
          photo_author='高参88',photographer='高参88',photographic_date='2013-09-14 (EXIF, principal northeast view)',
          geometry_license='MIT',texture_license='MIT',photos_embedded=False,viewer_page=SLUG+'.html',
          scope='双圆主楼朝花园的立面和阳台。其他同址楼房、后墙、屋面深处和室内尚缺同等的建筑资料。')
if (HERE/'cameras.json').is_file():
    META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in FINISHES:map_finish(self.parts[-1])

    def save(self,path,metadata=None):
        super().save(path,metadata)
        return embed_normals(path)

def add_building(builder,lod=False):
    add_central_front(builder,lod)
    add_southwest_colonnade(builder,lod)
    add_northeast_ground(builder,lod)
    add_winter_gardens(builder,lod)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--lod',action='store_true')
    args=parser.parse_args()
    builder=Builder(PALETTE);add_building(builder,args.lod)
    print(builder.save(args.output,META)['sha256'])
