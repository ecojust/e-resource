"""Build the historic Shanghai High School auditorium exterior facing the Longmen Building."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(HERE.parent/'measurements'),str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),
              str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
import auditorium_entrance,auditorium_flank,auditorium_roof,finish_surfaces,south_front

ID='xuhui-shanghai-high-school-historic-auditorium'
SLUG='shanghai-high-school-historic-auditorium'
META=dict(id=ID,name='上海中学历史大礼堂',address='上海市徐汇区上中路400号',heritage_group='5D087',
          source='https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
          photo_source='https://pastvu.com/p/1872086',contemporary_photo='https://www.meipian.cn/547hqpfk',
          photo_author='1934年照由Guangchan转引国家图书馆条目，2020年照载于“大器”的回访图集',
          photos_embedded=False,geometry_license='MIT',texture_license='MIT',viewer_page=SLUG+'.html',
          scope='历史大礼堂朝龙门楼的入口、主立面、旧照可辨的东侧窗墙及现存中央屋顶。入口按2020年照片，东侧外檐及窗间依据1934年资料。')
if (HERE/'cameras.json').exists():META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())
PALETTE={**south_front.PALETTE,**auditorium_entrance.PALETTE,**auditorium_flank.PALETTE,
         **auditorium_roof.PALETTE,**finish_surfaces.PALETTE}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        old_count=len(self.parts)
        GeometryBuilder.add(self,vertices,faces,material,label)
        if len(self.parts)>old_count and material in finish_surfaces.SURFACES:
            finish_surfaces.map_finish(self.parts[-1])
    def save(self,path,metadata=None):
        if any(self.palette[p['material']].get('texture') for p in self.parts):
            super().save(path,metadata)
            return finish_surfaces.embed_normals(path)
        return GeometryBuilder.save(self,path,metadata)
def add_building(b,lod=False):
    south_front.build_south(b,lod)
    south_front.porch_structure(b)
    south_front.raised_center(b)
    auditorium_entrance.add_entrance(b,lod)
    auditorium_flank.add_flank(b,lod)
    auditorium_roof.add_roof(b,lod)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    a=cli.parse_args();b=Builder(PALETTE);add_building(b,a.lod);print(b.save(a.output,META)['sha256'])
