"""Build the observed courtyard fronts of No. 313, South Xiangyang Road, after repair."""
import argparse
import json
import numpy as np
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(HERE.parent/'measurements'),
               str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),
               str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
from plan_points import load as load_plan
import foreground_bay
import service_balcony
import setback_wall
import canopy_front
import plaster_finishes
ID='xuhui-xiangyang-313-restored-courtyard-fronts'
SLUG='xiangyang-313-restored-courtyard-fronts'
PALETTE=(foreground_bay.PALETTE | service_balcony.PALETTE | setback_wall.PALETTE |
         canopy_front.PALETTE | plaster_finishes.PALETTE)
META={'id':ID,'name':'襄阳南路313号修缮后住宅院面','address':'上海市徐汇区襄阳南路313号',
      'heritage_id':'sh-historic-b5-xh-j-103-v','heritage_group':'5D103',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'http://www.shwfjz.com/showcase/3/',
      'photo_author':'上海维方建筑装饰工程有限公司，案例3修缮后实景。原照权利归原作者。',
      'photos_embedded':False,'geometry_license':'MIT','texture_license':'MIT','viewer_page':SLUG+'.html',
      'local_axes':'East, north, up (metres). Footprint 3304. The datum is the street level.',
      'camera_views':json.loads((HERE/'cameras.json').read_bytes()),
      'scope':'两处施工院面的格窗、百叶、阳台、雨篷、接水管、外机与安装托脚。'}

class Builder(CrownBuilder):
    def save(self,path,metadata=None):
        GeometryBuilder.save(self,path,metadata)
        return plaster_finishes.embed_normals(path)

def add_building(builder,lod=False):
    plan=load_plan()
    surfaces={'case1':(foreground_bay.add_foreground_bay,setback_wall.add_setback_wall,
                       service_balcony.add_service_balcony),
              'case2':(canopy_front.add_canopy_front,)}
    for name,components in surfaces.items():
        transform=np.asarray(plan['facade_frames'][name]['local_to_ENU'])
        local=GeometryBuilder(PALETTE)
        for add in components:add(local,lod)
        for part in local.parts:
            coords=np.asarray(part['vertices'])@transform[:3,:3].T+transform[:3,3]
            builder.add(coords,part['triangles'],part['material'],part['label'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod)
    print(b.save(a.output,META)['sha256'])
