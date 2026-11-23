"""Build the documented curved wing and the separate tiled entrance at 325 Changle Road."""
import argparse
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(HERE.parent/'measurements'),str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),
               str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
from register_porch import PorchFrame
import curved_wing
import porch_stone
import porch_tiles
import porch_doors
import porch_finishes

ID='xuhui-changle-325-garden-courtyard-and-arched-porch'
SLUG='changle-325-garden-courtyard-and-arched-porch'
PALETTE=curved_wing.PALETTE|porch_stone.PALETTE|porch_tiles.PALETTE|porch_doors.PALETTE|porch_finishes.PALETTE
META={'id':ID,'name':'长乐路325号院内弧窗与红瓦券廊','address':'上海市徐汇区长乐路325号，名录同时登记陕西南路164号',
      'heritage_id':'sh-historic-b5-xh-j-111-v','heritage_group':'5D111','viewer_page':SLUG+'.html',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'https://commons.wikimedia.org/wiki/Special:Redirect/page/39388838',
      'camera_views':json.loads((HERE/'cameras.json').read_bytes()),
      'photo_author':'Fayhoo, 2015-04-04, CC BY-SA 3.0','photos_embedded':False,
      'geometry_license':'CC BY-SA 3.0','texture_license':'CC BY-SA 3.0',
      'scope':'院内弧形窗墙及挑带、券廊的前脸与瓦坡、门扇、十级石阶和两侧栏杆。'}
class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        count=len(self.parts)
        super().add(vertices,faces,material,label)
        if len(self.parts)>count and material in porch_finishes.STEMS:porch_finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        GeometryBuilder.save(self,path,metadata)
        return porch_finishes.writer.embed_normals(path)

def add_building(b,lod=False):
    frame=PorchFrame()
    curved_wing.add_curved_wing(b,lod=lod)
    porch_stone.add_porch_stone(b,frame,lod=lod)
    porch_tiles.add_porch_roof(b,frame,lod=lod)
    porch_doors.add_porch_doors(b,frame,lod=lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod);print(b.save(a.output,META)['sha256'])
