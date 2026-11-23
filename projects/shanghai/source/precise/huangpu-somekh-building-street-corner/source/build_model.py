"""Rebuild the Beijing Road facade, entrance axis and corner of the Somekh Building."""
import argparse,json,os,sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE));sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
import package_architectural_model
from aggregate_mesh import AggregateBuilder
package_architectural_model.Builder=AggregateBuilder
from package_architectural_model import build
from photo_architecture import Facade
from finish import PALETTE,WALL,texture_uv
from main_portal import PORTAL_MATERIALS,add_portal
from south_front import front_run,staircase
from street_corner import add_corner,REG
import numpy as np

ID='huangpu-somekh-building-street-corner'
SCOPE='北京东路南街墙八个普通窗跨及中央主门、楼梯间和山花，东南圆门廊及修复的露天鼓座，四川中路紧邻转角的一个开间。'
META={'id':ID,'name':'沙美大楼北京东路主立面与四川中路转角','viewer_page':'somekh-building-street-corner.html',
      'status':'restored-street-facade-and-corner','model_scope_zh':SCOPE,'scope':SCOPE,'reference_height_m':29.95,
      'estimated':'直墙34.22米按OSM弧线拟合；立面各轴及高度依据修缮后照片投影估计；楼层与外挑深度未获实测。','interiors_modeled':False,
      'source_register':'source/precise/'+ID+'/reference-review.json','coordinate_convention':'Metres, Z up. X runs east along Beijing Road from the western boundary; Y points into the building.',
      'copyright':'Original architectural geometry and aggregate texture, MIT. The fascia font subset has separate SIL OFL 1.1 licensing. Reference photographs are credited and remain external.'}
PALETTE.update(PORTAL_MATERIALS)
LEVELS=[(6.33,8.86),(10.15,12.89),(14.48,16.92),(18.68,20.91)]
PARAPET=23.48

def add_building(builder,lod):
    length=REG['south_tangent_length_m']
    face=Facade(builder,(0.,0.),(length,0.),'Beijing Road')
    measurements=json.loads((SOURCE/'south-front-metrics.json').read_text())['planes']
    ground=[v['x_m']-length/2 for v in measurements['ground']['axes']]
    upper=[v['x_m']-length/2 for v in measurements['body']['axes']]
    openings=[(g,u,i in (0,8))for i,(g,u)in enumerate(zip(ground,upper))]
    main=ground[4]
    for start,end,positions in [(-length/2,main-2.18,openings[:4]),(main+2.18,length/2,openings[5:])]:
        front_run(face,start,end,positions,lod,LEVELS,PARAPET,setback=1.08)
    staircase(face,main,lod,add_portal)
    east_start=np.array(REG['east_tangent_start_m'])
    east_length=REG['east_bay_length_m']
    east=Facade(builder,east_start,east_start+np.array(REG['east_unit'])*east_length,'Sichuan Road')
    front_run(east,-east_length/2,east_length/2,[(0.,0.,True)],lod,LEVELS,PARAPET)
    add_corner(builder,lod,LEVELS,PARAPET)
    for part in builder.parts:
        if part['material']==WALL:
            part['texcoords']=[(u,1-v)for u,v in (texture_uv(*point)for point in part['vertices'])]

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--blender',default='blender')
    opts,rest=parser.parse_known_args()
    os.environ['SOMEKH_BLENDER']=opts.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
