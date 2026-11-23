"""Build the registered Wanping Road street block at number 42."""
import argparse
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
for relative in ('hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source','xuhui-gaoan-77-curved-veranda/source'):
    sys.path.append(str(PROJECT/'source/precise'/relative))
from crown_builder import CrownBuilder
from placement import Facade
from street_materials import PALETTE as SURFACES
from brick_finishes import PALETTE as BRICKS, REPEAT_METRES, embed_normals
from four_window_bays import add_bays
from brick_street import add_street

ID='xuhui-wanping-42-brick-window-bays'
SLUG='wanping-42-brick-window-bays'
SCALE=1.0
PALETTE={**SURFACES,**BRICKS}
META={'id':ID,'name':'宛平路42号住宅双色砖墙与卷叶凸窗','address':'上海市徐汇区宛平路42号',
      'heritage_group':'5D055','photo_reference':'https://commons.wikimedia.org/wiki/File:42_Wanping_Road.jpg',
      'photographer':'Livelikerw','photo_date':'2019-02-23','photo_reference_license':'CC BY-SA 4.0',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'texture_license':'MIT','geometry_license':'MIT','photos_embedded':False,
      'scope':'临街两层黄砖、两层红砖、四组折面凸窗、中央双列楼梯窗、门楣浮饰与连续卷纹花带。'}

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add([tuple(v*SCALE for v in p) for p in vertices],faces,material,label)
        if material in REPEAT_METRES:
            width,height=REPEAT_METRES[material]
            part=self.parts[-1]
            part['texcoords']=[(u/(.78*width*SCALE),v/(.78*height*SCALE)) for u,v in part['texcoords']]

    def save(self,path,metadata=None):
        super().save(path,metadata)
        return embed_normals(path)

def add_building(b,lod=False):
    front=Facade(b,label='Wanping Road | 42')
    add_street(front,lod)
    add_bays(b,lod)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lod',action='store_true')
    a=p.parse_args()
    b=Builder(PALETTE)
    add_building(b,a.lod)
    print(b.save(a.output,META)['sha256'])
