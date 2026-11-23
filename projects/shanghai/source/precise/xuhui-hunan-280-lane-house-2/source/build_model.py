"""Build the surveyed exterior of No. 2, Lane 280, Hunan Road."""
import argparse
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(HERE.parent/'measurements'),str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),
              str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
import house_finishes
import registered_walls
import flat_windows
import exterior_fittings
import curved_corner
import entrance

ID='xuhui-hunan-280-lane-house-2'
SLUG='hunan-280-lane-house-2'
PALETTE={**exterior_fittings.PALETTE,**flat_windows.PALETTE,**registered_walls.PALETTE,**curved_corner.PALETTE,**entrance.PALETTE,**house_finishes.PALETTE}
META={'id':ID,'name':'湖南路280弄2号五层住宅临街窗墙与弧窗','address':'上海市徐汇区湖南路280弄2号',
      'heritage_id':'sh-historic-b5-xh-j-115-v','heritage_group':'5D115','viewer_page':SLUG+'.html',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'https://4travel.jp/travelogue/11116083','photo_author':'中国の風景, 2016-03-13',
      'photos_embedded':False,'geometry_license':'MIT','texture_license':'MIT',
      'scope':'湖南路一侧的五层窗墙、斜向弄堂墙、四层转角钢窗和下方带2号门牌的入口。'}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        before=len(self.parts)
        super().add(vertices,faces,material,label)
        if len(self.parts)>before and material in house_finishes.STEMS:
            house_finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        GeometryBuilder.save(self,path,metadata)
        return house_finishes.writer.embed_normals(path)
def add_building(b,lod=False):
    registered_walls.add_registered_walls(b,lod)
    curved_corner.add_curved_corner(b,lod)
    entrance.add_entrance(b,lod)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    args=cli.parse_args();b=Builder(PALETTE);add_building(b,args.lod);print(b.save(args.output,META)['sha256'])
