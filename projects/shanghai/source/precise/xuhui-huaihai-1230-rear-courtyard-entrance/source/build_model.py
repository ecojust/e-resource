"""Build the photographed part of the rear courtyard elevation at 1230 Middle Huaihai Road."""
from pathlib import Path
import argparse
import json
import sys

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),
              str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
import court_front
import courtyard_balconies
import court_finishes

ID='xuhui-huaihai-1230-rear-courtyard-entrance'
SLUG='huaihai-1230-rear-courtyard-entrance'
PALETTE={**courtyard_balconies.PALETTE,**court_front.PALETTE,**court_finishes.PALETTE}
META=dict(id=ID,name='淮海中路后排1230号入口与叠层阳台',address='上海市徐汇区淮海中路1230号院内',
          heritage_id='sh-historic-b5-xh-j-095-v',heritage_group='5D095',
          source='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          photo_source='https://4travel.jp/travelogue/11115719',photo_author='高参88（2013年图文）及中国の風景（2016年1月20日）',
          photos_embedded=False,geometry_license='MIT',texture_license='MIT',viewer_page=SLUG+'.html',
          local_axes='X along courtyard front toward ENE; positive Y inward NNW; Z above the court walk.',
          scope='后排1230号门洞、台阶、相邻暖色砖窗墙和门右的四层叠台，开合及封窗采用2016年院内照片，细部对照2013年近照。')
if (HERE/'cameras.json').exists():META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        start=len(self.parts)
        GeometryBuilder.add(self,vertices,faces,material,label)
        if len(self.parts)>start and material in court_finishes.SURFACES:
            court_finishes.map_finish(self.parts[-1])

    def save(self,path,metadata=None):
        super().save(path,metadata)
        return court_finishes.embed_normals(path)

def add_building(builder,lod=False):
    court_front.add_front(builder,lod)
    courtyard_balconies.add_balconies(builder,lod)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args()
    builder=Builder(PALETTE);add_building(builder,args.lod)
    print(builder.save(args.output,META)['sha256'])
