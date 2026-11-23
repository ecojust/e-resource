"""Reconstruct the visible street facade of the green residence at 2 Yanqing Road."""
import argparse
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.append(str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.append(str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
from residence_finishes import PALETTE as FINISHES, map_finish, embed_normals
from street_roof import PALETTE as ROOF, add_roof
from central_stair import add_stair, PALETTE as STAIR
from street_bays import add_bays,PALETTE as BAYS,bay_wall_cutouts
from street_entry import add_entry,PALETTE as ENTRY
from street_frontage import add_joining_walls
ID='xuhui-yanqing-2-green-street-residence'
SLUG='yanqing-2-green-street-residence'
PALETTE={**BAYS,**ENTRY,**STAIR,**ROOF,**FINISHES}
META={'id':ID,'name':'延庆路2号浅绿住宅与弧形楼梯间','address':'上海市徐汇区延庆路2号',
      'heritage_group':'5D067','photo_author':'Fayhoo','photo_date':'2015-06-21',
      'photo_source':'https://commons.wikimedia.org/wiki/File:Yanqinglu_2_Hao_Zhuzhai.JPG',
      'photo_reference_license':'CC BY-SA 3.0','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'scope':'延庆路2号所在临街楼体的浅绿立面、三级楼梯窗、成组凸窗、两层阳台与绿色入口。'}
META.update(camera_views=json.loads((HERE/'cameras.json').read_text()),viewer_page=SLUG+'.html')

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in FINISHES:
            map_finish(self.parts[-1])

    def save(self,path,metadata=None):
        super().save(path,metadata)
        return embed_normals(path)

def add_building(b,lod=False):
    holes=[v for v in bay_wall_cutouts() if .60<v.centroid.x<2 and v.bounds[3]<3.5]
    add_stair(b,lod,holes)
    add_joining_walls(b,lod)
    add_bays(b,lod)
    add_entry(b,lod,{'right_wall_y':2.40})
    add_roof(b,lod)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true')
    a=cli.parse_args();b=Builder(PALETTE);add_building(b,a.lod);print(b.save(a.output,META)['sha256'])
